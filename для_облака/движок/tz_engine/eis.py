"""Разбор структурированного извещения ЕИС (44-ФЗ).

Поддерживаются:
* JSON извещения в том виде, как его отдаёт открытое API ГосПлан
  (GET /fz44/purchases/{номер}/notification) — внутри поле "source" с документом ЕИС;
* XML извещения ЕИС (epNotificationEF2020, epNotificationEZK2020 и т. п.,
  как их выгружает ЕИС через FTP/СМЭВ или печатную форму).

Позиции с КТРУ содержат характеристики с условиями прямо в извещении —
это самый надёжный источник: регулярные выражения не нужны.
"""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from . import units
from .conditions import detect_equiv, parse_value
from .models import Position, Purchase, Requirement, fmt

try:
    REGIONS = json.loads((Path(__file__).parent / "data" / "regions.json").read_text("utf-8"))
except OSError:
    REGIONS = {}

SOURCE_GOSPLAN = "структурированное извещение ЕИС (через открытое API ГосПлан)"

PLACING = {
    "EA20": "Электронный аукцион", "EAP20": "Электронный аукцион", "EAB20": "Электронный аукцион",
    "ZKP20": "Запрос котировок в электронной форме", "ZK20": "Запрос котировок в электронной форме",
    "OK20": "Открытый конкурс в электронной форме", "OKP20": "Открытый конкурс в электронной форме",
}


def L(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def g(d, *path, default=None):
    for p in path:
        if isinstance(d, list):
            d = d[0] if d else None
        if not isinstance(d, dict):
            return default
        d = d.get(p)
    return default if d is None else d


# ------------------------------------------------------------- XML -> dict

def _strip(tag: str) -> str:
    return tag.split("}", 1)[-1]


def xml_to_dict(el: ET.Element):
    children = list(el)
    if not children:
        return (el.text or "").strip()
    out: dict = {}
    for ch in children:
        k = _strip(ch.tag)
        v = xml_to_dict(ch)
        if k in out:
            if not isinstance(out[k], list):
                out[k] = [out[k]]
            out[k].append(v)
        else:
            out[k] = v
    return out


def load_notice(path: str | Path) -> tuple[dict, dict]:
    """Вернуть (документ извещения, метаданные). Понимает JSON ГосПлан и XML ЕИС."""
    p = Path(path)
    data = p.read_bytes()
    meta: dict = {}
    if p.suffix.lower() == ".xml" or data.lstrip()[:1] == b"<":
        root = ET.fromstring(data)
        doc = xml_to_dict(root)
        meta["doc_type"] = _strip(root.tag)
        meta["format"] = "eis-xml"
        return doc, meta
    obj = json.loads(data.decode("utf-8"))
    meta["format"] = "eis-json"
    if isinstance(obj, dict):
        meta.update(obj.get("_meta", {}))
        if meta.get("region_code") not in (None, ""):
            meta["region"] = REGIONS.get(str(meta["region_code"]), str(meta["region_code"]))
        if "source223" in obj:
            meta["doc_type"] = obj.get("doc_type", "")
            meta["format"] = "eis223-json"
            return obj["source223"], meta
        if "source" in obj:
            meta["doc_type"] = obj.get("doc_type", "")
            return obj["source"], meta
    return obj, meta


def looks_like_notice(path: str | Path) -> bool:
    p = Path(path)
    if p.suffix.lower() not in (".json", ".xml"):
        return False
    head = p.read_bytes()[:4000].decode("utf-8", "ignore")
    return "purchaseNumber" in head or "notificationInfo" in head or "epNotification" in head or '"source"' in head


# --------------------------------------------------------- характеристики

def _okei_unit(v: dict) -> str:
    okei = v.get("OKEI") or {}
    nc = okei.get("nationalCode") or ""
    if nc and units.lookup(nc):
        return nc
    code = okei.get("code")
    if code and code in units.OKEI_CODE:
        return units.OKEI_CODE[code]
    name = okei.get("name") or ""
    if name and units.lookup(name):
        return name
    return nc


def char_to_requirement(c: dict) -> Requirement:
    name = (c.get("name") or "").strip()
    instr = g(c, "characteristicsFillingInstruction", "name", default="") or ""
    icode = str(g(c, "characteristicsFillingInstruction", "code", default="") or "")
    vals = L(g(c, "values", "value"))
    r = Requirement(name=name, instruction=instr)
    texts, ranges, concrete = [], [], []
    unit = ""
    for v in vals:
        if not isinstance(v, dict):
            continue
        u = _okei_unit(v)
        unit = unit or u
        if v.get("qualityDescription"):
            texts.append(str(v["qualityDescription"]).strip())
        rs = g(v, "rangeSet", "valueRange")
        if rs:
            for rr in L(rs):
                ranges.append(rr)
        cv = g(v, "valueSet", "concreteValue")
        if cv not in (None, ""):
            for x in L(cv):
                concrete.append(x)
    if not unit:
        unit = units.unit_from_header(name) or ""
    r.unit = unit

    if ranges:
        rr = ranges[0]
        mn, mx = rr.get("min"), rr.get("max")
        mnn, mxn = rr.get("minMathNotation", ""), rr.get("maxMathNotation", "")
        vmin = float(str(mn).replace(",", ".")) if mn not in (None, "") else None
        vmax = float(str(mx).replace(",", ".")) if mx not in (None, "") else None
        r.vmin, r.vmax = vmin, vmax
        r.min_strict = mnn == "greater"
        r.max_strict = mxn == "less"
        if vmin is not None and vmax is not None:
            r.op = "диапазон"
            r.value = f"{fmt(vmin)}–{fmt(vmax)}"
        elif vmin is not None:
            r.op = ">="
            r.value = fmt(vmin)
        else:
            r.op = "<="
            r.value = fmt(vmax)
        r.raw = r.describe()
        return r
    if concrete:
        try:
            nums = [float(str(x).replace(",", ".")) for x in concrete]
        except ValueError:
            nums = []
        if len(nums) == 1:
            r.op, r.vmin, r.vmax = "=", nums[0], nums[0]
            r.value = fmt(nums[0])
            r.raw = r.describe()
            return r
        if nums:
            r.op = "из_списка"
            r.values = [fmt(n) for n in nums]
            r.value = "; ".join(r.values)
            r.raw = r.value
            return r
    if texts:
        norm = []
        for t in texts:
            tl = t.lower().strip()
            norm.append("да" if tl in ("да", "наличие", "есть") else "нет" if tl in ("нет", "отсутствует") else t)
        if len(texts) == 1 and "разрешени" in name.lower() and "печат" not in name.lower() and "скан" not in name.lower():
            pr = parse_value(texts[0], name, unit)
            if pr.unit == "пиксель":
                pr.instruction = instr
                return pr
        if len(texts) == 1 and re.search(r"\d", texts[0]) and re.search(r"≥|≤|>|<|не менее|не более|от\s*\d|до\s*\d|более|менее|[xх×]\s*\d", texts[0].lower()):
            pr = parse_value(texts[0], name, unit)
            if pr.op in (">=", "<=", "диапазон") or pr.vmin is not None or (pr.values and pr.unit == "пиксель"):
                pr.instruction = instr
                return pr
        r.values = norm
        if len(norm) == 1:
            r.op = "="
        elif icode in ("5", "6") or "все значения" in instr.lower() or "не может изменяться" in instr.lower():
            # «не может изменяться» + несколько значений = товар должен иметь все перечисленные
            r.op, r.all_values = "=", True
        else:
            r.op = "из_списка"
        r.value = (" + " if r.all_values else "; ").join(norm)
        r.raw = "; ".join(texts)
        eq = detect_equiv(r.raw)
        if eq is not None:
            r.equiv = eq
        return r
    r.op, r.value = "текст", ""
    return r


def _chars(obj: dict) -> list[Requirement]:
    out = []
    ch = obj.get("characteristics") or {}
    for kind in ("characteristicsUsingReferenceInfo", "characteristicsUsingTextForm"):
        for c in L(ch.get(kind)):
            if isinstance(c, dict):
                out.append(char_to_requirement(c))
    return out


BRAND_RE = re.compile(r"\b(Panasonic|Canon|HP|Hewlett|Kyocera|Xerox|Brother|Epson|Lenovo|Dell|Huawei|Cisco|Samsung|Ricoh|Sharp|Avaya|Yealink|Logitech|Jabra|Pantum|Konica|Intel|AMD|Asus|Acer|Apple|Microsoft|Mikrotik|D-Link|TP-Link|Eltex|Qtech|ProTone\w*)\b", re.I)


def parse_notice_doc(doc: dict, meta: dict | None = None) -> Purchase:
    meta = meta or {}
    ci = doc.get("commonInfo") or {}
    ni = doc.get("notificationInfo") or {}
    pur = Purchase()
    pur.number = str(ci.get("purchaseNumber") or meta.get("purchase_number") or "")
    pur.subject = (ci.get("purchaseObjectInfo") or "").strip()
    pur.method = g(ci, "placingWay", "name", default="") or PLACING.get(g(ci, "placingWay", "code", default=""), "")
    pur.url = ci.get("href") or (f"https://zakupki.gov.ru/epz/order/notice/ea20/view/common-info.html?regNumber={pur.number}" if pur.number else "")
    cust = g(ni, "customerRequirementsInfo", "customerRequirementInfo", "customer", "fullName", default="")
    if not cust:
        cust = g(doc, "purchaseResponsibleInfo", "responsibleOrgInfo", "fullName", default="")
    pur.customer = cust
    pur.customer_inn = str(meta.get("customer_inn") or "")
    mp = g(ni, "contractConditionsInfo", "maxPriceInfo", "maxPrice")
    try:
        pur.nmc = float(mp) if mp not in (None, "") else None
    except (TypeError, ValueError):
        pur.nmc = None
    pur.deadline = g(ni, "procedureInfo", "collectingInfo", "endDT", default="") or ""
    pur.region = str(meta.get("region") or "")
    pur.source = meta.get("source") or SOURCE_GOSPLAN
    pur.parser = meta.get("format", "eis-json")

    poi = g(ni, "purchaseObjectsInfo", "notDrugPurchaseObjectsInfo", default={}) or {}
    restrict = False
    for i, po in enumerate(L(poi.get("purchaseObject")), 1):
        if not isinstance(po, dict):
            continue
        k = po.get("KTRU") or {}
        o = po.get("OKPD2") or {}
        pos = Position(num=i, name=(po.get("name") or k.get("name") or o.get("OKPDName") or "").strip())
        pos.ktru = k.get("code") or ""
        pos.okpd2 = g(k, "OKPD2", "OKPDCode", default="") or o.get("OKPDCode") or ""
        q = g(po, "quantity", "value")
        try:
            pos.quantity = float(q) if q not in (None, "") else None
        except (TypeError, ValueError):
            pos.quantity = None
        pos.unit = g(po, "OKEI", "nationalCode", default="шт") or "шт"
        try:
            pos.price = float(po.get("price")) if po.get("price") else None
        except (TypeError, ValueError):
            pos.price = None
        pos.requirements = _chars(k) + _chars(o)
        if str(g(po, "restrictionsInfo", "isRestrictForeignPurchaseObjects", default="")).lower() == "true":
            restrict = True
        m = BRAND_RE.search(pos.name)
        if m and not detect_equiv(pos.name):
            pos.brand_no_equiv = True
            for r in pos.requirements:
                r.equiv = False
            pos.note = f"в наименовании указан товарный знак «{m.group(1)}» без «или эквивалент»"
        pur.positions.append(pos)
    pur.foreign_restriction = restrict
    return pur


def parse_223_doc(doc: dict, meta: dict) -> Purchase:
    """Извещение 223-ФЗ: позиции есть (ОКПД2, количество), характеристик в извещении нет."""
    pur = Purchase(law="223-ФЗ", parser="eis223-json")
    pur.number = str(doc.get("registrationNumber") or meta.get("purchase_number") or "")
    pur.subject = doc.get("name") or ""
    pur.customer = g(doc, "customer", "mainInfo", "fullName", default="")
    pur.customer_inn = g(doc, "customer", "mainInfo", "inn", default="") or meta.get("customer_inn", "")
    pur.method = doc.get("purchaseCodeName") or ""
    pur.url = doc.get("urlEIS") or ""
    pur.deadline = doc.get("submissionCloseDateTime") or ""
    pur.region = meta.get("region", "")
    pur.source = meta.get("source") or SOURCE_GOSPLAN
    restrict = False
    for lot in L(g(doc, "lots", "lot")):
        try:
            pur.nmc = (pur.nmc or 0) + float(g(lot, "lotData", "initialSum", default=0) or 0)
        except (TypeError, ValueError):
            pass
        for it in L(g(lot, "lotData", "lotItems", "lotItem")):
            pos = Position(num=len(pur.positions) + 1, name=g(it, "okpd2", "name", default="") or "")
            pos.okpd2 = g(it, "okpd2", "code", default="") or ""
            try:
                pos.quantity = float(it.get("qty")) if it.get("qty") else None
            except (TypeError, ValueError):
                pass
            pos.unit = "шт" if g(it, "okei", "code") == "796" else (g(it, "okei", "name", default="") or "")
            pos.note = "характеристики в извещении 223-ФЗ не указаны — они в документации закупки"
            if str(it.get("constraintNationalRegime", "")).lower() == "true" or str(it.get("prohibitionNationalRegime", "")).lower() == "true":
                restrict = True
            pur.positions.append(pos)
    pur.foreign_restriction = restrict
    return pur


def parse_notice_file(path: str | Path, meta: dict | None = None) -> Purchase:
    doc, m = load_notice(path)
    if meta:
        m.update(meta)
    if m.get("format") == "eis223-json":
        return parse_223_doc(doc, m)
    return parse_notice_doc(doc, m)
