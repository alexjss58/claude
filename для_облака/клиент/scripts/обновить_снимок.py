#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Обновить снимок актуальных тендеров для клиентского сайта «Тендер под ключ».

Как запустить (из папки клиент/):
    python3 scripts/обновить_снимок.py              # полный цикл
    python3 scripts/обновить_снимок.py --без-извещений   # только списки (быстро, без позиций)
    python3 scripts/обновить_снимок.py --заново     # сбросить кэш извещений
Сколько это займёт: ~35-45 минут. Лимит открытого API ГосПлан — 10 запросов в минуту,
скрипт держит паузу 6,5 с между запросами: ~25 запросов на списки (3-4 мин) и до ~225
запросов на извещения 44-ФЗ (~25-30 мин). Прервали — запустите снова: уже скачанные
извещения лежат в data/_кэш/ и повторно не качаются. Во время работы каждые 20 извещений
пишется промежуточный data/снимок.json.

Что делает:
 1. Списки закупок 44-ФЗ и 223-ФЗ по ОКПД2-префиксам ниш (stage=1, подача открыта до
    5 ноября 2026 12:00 МСК, опубликованы за последние 30 дней).
 2. Отсев работ и услуг по названию (результаты/фильтр_закупок.py, функция классифицировать).
 3. Для 44-ФЗ (НМЦ 100 тыс. - 20 млн ₽, по ~45 на нишу) скачивает извещение и разбирает позиции и
    характеристики движком движок/tz_engine. Контакты сотрудников заказчика удаляются (scrub).
 4. Пишет data/снимок.json, data/регионы.json, data/СНИМОК.md.
Если API недоступно или вернуло мусор, скрипт завершается с кодом 1 и ничего не затирает.

ВАЖНО про время: API ГосПлан отдаёт время в UTC. В снимке всё переведено в московское (UTC+3).
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLIENT = HERE.parent
DATA = CLIENT / "data"
CACHE = DATA / "_кэш"
ROOT = CLIENT.parent                       # для_облака/
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "результаты"))
sys.path.insert(0, str(ROOT / "движок" / "инструменты"))

from движок.tz_engine import eis                      # noqa: E402  разбор извещения
from движок.tz_engine.units import pretty_unit        # noqa: E402
from фильтр_закупок import классифицировать           # noqa: E402
from получить_закупки import scrub                    # noqa: E402  удаление личных данных

BASE = "https://v2test.gosplan.info"
MSK = timezone(timedelta(hours=3))
GAP = 6.5                                  # секунд между запросами (лимит 10/мин)

# Конец подачи не раньше (МСК). Опубликовано не раньше N дней назад.
DEADLINE_MSK = datetime(2026, 11, 5, 12, 0)
PUBLISHED_DAYS = 30
MAX_PER_NICHE = 150                        # потолок на нишу, чтобы ниши были примерно равны
NOTICE_PER_NICHE = 45
NOTICE_NMC = (100_000, 20_000_000)

NICHES = {                                 # ниша -> ОКПД2-префиксы
    "Компьютеры и оргтехника": ["26.20", "28.23"],
    "Связь и сети": ["26.30"],
    "Аудио- и видеотехника": ["26.40"],
    "Измерительные приборы": ["26.51"],
    "Лабораторные реактивы": ["20.59.52"],
}

# purchase_type (ГосПлан) -> способ определения поставщика
SPOSOB = {
    # 44-ФЗ
    "epNotificationEF2020": "Электронный аукцион",
    "epNotificationEZK2020": "Запрос котировок в электронной форме",
    "epNotificationEOK2020": "Открытый конкурс в электронной форме",
    "epNotificationEOKOU2020": "Конкурс с ограниченным участием в электронной форме",
    "epNotificationEOKD2020": "Двухэтапный конкурс в электронной форме",
    "epNotificationEZP2020": "Запрос предложений в электронной форме",
    "epNotificationEP2020": "Закупка у единственного поставщика (электронная)",
    # 223-ФЗ
    "purchaseNotice": "Закупка (извещение 223-ФЗ)",
    "purchaseNoticeAE": "Аукцион в электронной форме",
    "purchaseNoticeAESMBO": "Аукцион в электронной форме (для СМП)",
    "purchaseNoticeAE94": "Аукцион в электронной форме",
    "purchaseNoticeEP": "Закупка у единственного поставщика",
    "purchaseNoticeIS": "Закупка у единственного поставщика",
    "purchaseNoticeKESMBO": "Конкурс в электронной форме (для СМП)",
    "purchaseNoticeOA": "Открытый аукцион",
    "purchaseNoticeOK": "Открытый конкурс",
    "purchaseNoticeOKESMBO": "Открытый конкурс в электронной форме (для СМП)",
    "purchaseNoticeOK504": "Открытый конкурс",
    "purchaseNoticeZK": "Запрос котировок",
    "purchaseNoticeZKESMBO": "Запрос котировок в электронной форме (для СМП)",
    "purchaseNoticeZKB": "Запрос котировок",
    "purchaseNoticeZP": "Запрос предложений",
    "purchaseNoticeZPESMBO": "Запрос предложений в электронной форме (для СМП)",
    "purchaseNoticeOKU": "Конкурс с ограниченным участием",
    "purchaseNoticeOKD": "Двухэтапный конкурс",
    "purchaseNoticeOKUESMBO": "Конкурс с ограниченным участием в электронной форме (для СМП)",
    "purchaseNoticeOKDESMBO": "Двухэтапный конкурс в электронной форме (для СМП)",
    "purchaseNoticeAESMBO223": "Аукцион в электронной форме (для СМП)",
}
# Ссылка ЕИС 44-ФЗ: каталог в адресе зависит от способа
EIS44_PATH = {
    "epNotificationEF2020": "ea20", "epNotificationEZK2020": "zk20", "epNotificationEOK2020": "ok20",
    "epNotificationEOKOU2020": "okou20", "epNotificationEOKD2020": "okd20", "epNotificationEZP2020": "zp20",
}

# Федеральные округа по коду субъекта (код ЕИС = код субъекта РФ)
ФО = {
    "Центральный": [31, 32, 33, 36, 37, 40, 44, 46, 48, 50, 57, 62, 67, 68, 69, 71, 76, 77],
    "Северо-Западный": [10, 11, 29, 35, 39, 47, 51, 53, 60, 78, 83],
    "Южный": [1, 8, 23, 30, 34, 61, 90, 91, 92, 93, 94, 95],
    "Северо-Кавказский": [5, 6, 7, 9, 15, 20, 26],
    "Приволжский": [2, 12, 13, 16, 18, 21, 43, 52, 56, 58, 59, 63, 64, 73],
    "Уральский": [45, 66, 72, 74, 86, 89],
    "Сибирский": [4, 17, 19, 22, 24, 38, 42, 54, 55, 70],
    "Дальневосточный": [3, 14, 25, 27, 28, 41, 49, 65, 75, 79, 87],
}


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def die(msg: str):
    log("ОШИБКА:", msg)
    sys.exit(1)


# ------------------------------------------------------------------ HTTP

_last = [0.0]


def api(path: str, params: dict | None = None):
    """GET с паузой под лимит, повтором на 429 (25-60 с) и честным падением."""
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    fails = 0
    for attempt in range(12):
        wait = GAP - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as r:
                body = r.read()
            obj = json.loads(body)
            if isinstance(obj, dict) and obj.get("message") and "rate limit" in str(obj["message"]).lower():
                raise urllib.error.HTTPError(url, 429, "rate", {}, None)
            return obj
        except urllib.error.HTTPError as e:
            if e.code == 429:
                pause = random.randint(25, 60)
                log(f"429, жду {pause} с")
                time.sleep(pause)
                _last[0] = time.time()
                continue
            if e.code == 404:
                return None
            fails += 1
            log(f"HTTP {e.code} на {path}, попытка {attempt + 1}")
            time.sleep(10)
        except (OSError, ValueError) as e:
            fails += 1
            log(f"сбой {type(e).__name__} на {path}, попытка {attempt + 1}")
            time.sleep(10)
        if fails >= 5:
            break
    die(f"API ГосПлан недоступно или отвечает неверно: {url}")


# ------------------------------------------------------------------ время

def utc_to_msk(s: str | None) -> datetime | None:
    if not s:
        return None
    s = s.split("+")[0].rstrip("Z")
    for f in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, f).replace(tzinfo=timezone.utc).astimezone(MSK).replace(tzinfo=None)
        except ValueError:
            pass
    return None


# ------------------------------------------------------------------ списки

def fetch_list(law: str, prefix: str, now_utc: datetime) -> list[dict]:
    path = f"/{law}/purchases"
    after_key = "collecting_finished_after" if law == "fz44" else "submission_close_after"
    cutoff_utc = (DEADLINE_MSK - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%S")
    out, skip, limit = [], 0, 100
    while True:
        params = {"classifier": prefix, "stage": 1, after_key: cutoff_utc,
                  "published_after": (now_utc - timedelta(days=PUBLISHED_DAYS)).strftime("%Y-%m-%d"),
                  "limit": limit, "skip": skip}
        page = api(path, params)
        if not isinstance(page, list):
            die(f"список {law} {prefix}: ожидался массив, получено {str(page)[:120]}")
        out += page
        log(f"  {law} {prefix}: страница skip={skip}, получено {len(page)}, всего {len(out)}")
        if len(page) < limit:
            break
        skip += len(page)
        if skip > 3000:
            break
    return out


def niche_of(codes: list[str], found_by: list[str]) -> str:
    """Ниша по кодам ОКПД2/КТРУ закупки (больше совпадений = ниша), при равенстве — по порядку запроса."""
    score = Counter()
    for c in codes:
        for n, prefs in NICHES.items():
            if any(c.startswith(p) for p in prefs):
                score[n] += 1
    if not score:
        for n in found_by:
            return n
        return ""
    best = max(score.values())
    for n in list(NICHES):
        if score[n] == best and (n in found_by or not found_by):
            return n
    return max(score, key=score.get)


def eis_link(law: str, number: str, ptype: str, href: str = "") -> str:
    if law == "44-ФЗ":
        if href:
            return href
        d = EIS44_PATH.get(ptype)
        if d:
            return f"https://zakupki.gov.ru/epz/order/notice/{d}/view/common-info.html?regNumber={number}"
    # без уверенности в формате — поиск ЕИС по номеру
    return f"https://zakupki.gov.ru/epz/order/extendedsearch/results.html?searchString={number}"


def flags_of(cls: dict) -> list[str]:
    fl = []
    if cls["тип"] == "смешанная":
        fl.append("смешанная: поставка + работы/услуги")
    if cls.get("под_своего"):
        fl.append("возможно под конкретного поставщика")
    for p in cls.get("признаки", []):
        if p.startswith("бренд_или_модель"):
            fl.append("бренд/модель в названии")
        elif p == "нет_или_эквивалент":
            fl.append("нет «или эквивалент»")
    return list(dict.fromkeys(fl))


def collect(now_utc: datetime) -> list[dict]:
    items: dict[str, dict] = {}
    for law in ("fz44", "fz223"):
        for niche, prefs in NICHES.items():
            for pref in prefs:
                log(f"список {law} {niche} ({pref})")
                for it in fetch_list(law, pref, now_utc):
                    n = it["purchase_number"]
                    rec = items.setdefault(n, {"raw": it, "law": "44-ФЗ" if law == "fz44" else "223-ФЗ", "found": []})
                    if niche not in rec["found"]:
                        rec["found"].append(niche)
    tenders = []
    stat = Counter()
    for n, rec in items.items():
        it = rec["raw"]
        end_key = "collecting_finished_at" if rec["law"] == "44-ФЗ" else "submission_close_at"
        end = utc_to_msk(it.get(end_key))
        pub = utc_to_msk(it.get("published_at"))
        if it.get("stage") != 1 or not end or end < DEADLINE_MSK:
            stat["не прошла по сроку/стадии"] += 1
            continue
        if pub and pub < datetime.now(MSK).replace(tzinfo=None) - timedelta(days=PUBLISHED_DAYS + 1):
            stat["старая публикация"] += 1
            continue
        cls = классифицировать(it.get("object_info") or "")
        if cls["тип"] == "работы_услуги":
            stat["работы/услуги"] += 1
            continue
        codes = list(it.get("okpd2") or []) + list(it.get("ktru") or [])
        niche = niche_of(codes, rec["found"])
        ptype = it.get("purchase_type") or ""
        t = {
            "номер": n, "закон": rec["law"],
            "способ": SPOSOB.get(ptype) or f"Иной способ ({ptype})",
            "предмет": (it.get("object_info") or "").strip(),
            "заказчик": None,
            "инн_заказчика": (it.get("customers") or [it.get("customer")] or [None])[0] or it.get("responsible") or it.get("placer"),
            "регион_код": it.get("region"), "регион": None,
            "нмц": it.get("max_price"),
            "обеспечение_заявки_проц": None,
            "обеспечение_контракта_проц": it.get("contract_guarantee_part"),
            "опубликовано": pub.strftime("%Y-%m-%d") if pub else None,
            "окончание_подачи": end.strftime("%Y-%m-%dT%H:%M:%S"),
            "окпд2": it.get("okpd2") or [], "ктру": it.get("ktru") or [],
            "ниша": niche, "тип": cls["тип"], "флаги": flags_of(cls),
            "ссылка": eis_link(rec["law"], n, ptype),
            "позиции": None,
            "_ptype": ptype,
        }
        if it.get("contract_guarantee_amount") is not None and it.get("contract_guarantee_part") is None:
            t["обеспечение_контракта_сумма"] = it["contract_guarantee_amount"]
        if rec["law"] == "223-ФЗ":
            t["позиции_пометка"] = "ТЗ в документах закупки"
        tenders.append(t)
    log("отсев:", dict(stat), "| осталось:", len(tenders))
    collect.stat = dict(stat)
    return tenders


def balance(tenders: list[dict]) -> list[dict]:
    """Не больше MAX_PER_NICHE на нишу. Порядок отбора: чередуем законы, свежие публикации раньше."""
    by = defaultdict(list)
    for t in tenders:
        by[t["ниша"]].append(t)
    out = []
    for niche, lst in by.items():
        if len(lst) <= MAX_PER_NICHE:
            out += lst
            continue
        a = sorted([t for t in lst if t["закон"] == "44-ФЗ"], key=lambda t: (t["опубликовано"] or ""), reverse=True)
        b = sorted([t for t in lst if t["закон"] == "223-ФЗ"], key=lambda t: (t["опубликовано"] or ""), reverse=True)
        pick = []
        while len(pick) < MAX_PER_NICHE and (a or b):
            for src in (a, b):
                if src and len(pick) < MAX_PER_NICHE:
                    pick.append(src.pop(0))
        out += pick
    return out


# ------------------------------------------------------------------ извещения

def position_dict(p, cap: int | None = None) -> dict:
    chars = []
    for r in p.requirements:
        u = pretty_unit(r.unit) if r.unit and r.unit != "пиксель" else (r.unit or "")
        chars.append({"имя": r.name, "условие": r.op, "значение": r.value or r.raw or "", "единица": u})
    if cap:
        chars = chars[:cap]
    return {"№": p.num, "наименование": p.name, "окпд2": p.okpd2 or None, "ктру": p.ktru or None,
            "количество": p.quantity, "единица": p.unit, "цена_за_ед": p.price, "характеристики": chars}


def get_notice(t: dict, redo: bool) -> dict | None:
    f = CACHE / f"{t['номер']}.json"
    if f.exists() and not redo:
        return json.loads(f.read_text("utf-8"))
    n = api(f"/fz44/purchases/{t['номер']}/notification")
    if not n or "source" not in n:
        return None
    doc = scrub(n["source"])
    meta = {"purchase_number": t["номер"], "customer_inn": t["инн_заказчика"] or ""}
    pur = eis.parse_notice_doc(doc, meta)
    ni = doc.get("notificationInfo") or {}
    cri = eis.g(ni, "customerRequirementsInfo", "customerRequirementInfo", default={}) or {}
    ag = eis.g(cri, "applicationGuarantee", "part")
    cg = eis.g(cri, "contractGuarantee", "part")
    res = {
        "заказчик": pur.customer or None,
        "способ": pur.method or None,
        "ссылка": pur.url or None,
        "обеспечение_заявки_проц": float(ag) if ag not in (None, "") else None,
        "обеспечение_контракта_проц": float(cg) if cg not in (None, "") else None,
        "позиции": [position_dict(p) for p in pur.positions],
    }
    CACHE.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(res, ensure_ascii=False), "utf-8")
    return res


def choose_for_notice(tenders: list[dict]) -> list[dict]:
    """44-ФЗ, НМЦ 100 тыс.-20 млн, по NOTICE_PER_NICHE на нишу; сначала закупки с КТРУ (там есть характеристики)."""
    out = []
    for niche in NICHES:
        c = [t for t in tenders if t["закон"] == "44-ФЗ" and t["ниша"] == niche and t["нмц"]
             and NOTICE_NMC[0] <= t["нмц"] <= NOTICE_NMC[1]]
        c.sort(key=lambda t: (bool(t["ктру"]), t["опубликовано"] or ""), reverse=True)
        out += c[:NOTICE_PER_NICHE]
    return out


# ------------------------------------------------------------------ выход

def regions_table() -> list[dict]:
    names = json.loads((ROOT / "движок" / "tz_engine" / "data" / "regions.json").read_text("utf-8"))
    fo_of = {}
    for fo, codes in ФО.items():
        for c in codes:
            fo_of[c] = fo
    rows = []
    for code, name in names.items():
        c = int(code)
        rows.append({"код": c, "название": name, "фо": fo_of.get(c, "вне ФО (Байконур)" if c == 99 else "не определён")})
    return sorted(rows, key=lambda r: r["код"])


def write_snapshot(tenders, regs, notice_cnt, now_msk, path: Path = None):
    names = {r["код"]: r["название"] for r in regs}
    out = []
    for t in tenders:
        t = {k: v for k, v in t.items() if not k.startswith("_")}
        t["регион"] = names.get(t["регион_код"])
        out.append(t)
    out.sort(key=lambda t: (list(NICHES).index(t["ниша"]) if t["ниша"] in NICHES else 99, t["окончание_подачи"]))
    snap = {"снято": now_msk.strftime("%Y-%m-%dT%H:%M:%S+03:00"),
            "источник": "ГосПлан API (открытое зеркало ЕИС), v2test.gosplan.info",
            "время": "московское (в API время в UTC, пересчитано +3 ч)",
            "ниши": list(NICHES), "тендеры": out}
    text = json.dumps(snap, ensure_ascii=False, indent=1)
    if len(text.encode()) > 6_000_000:
        for t in out:
            for p in t.get("позиции") or []:
                p["характеристики"] = p["характеристики"][:25]
        text = json.dumps(snap, ensure_ascii=False, indent=1)
    (path or DATA / "снимок.json").write_text(text, "utf-8")
    return snap


def write_report(snap, extra: dict):
    T = snap["тендеры"]
    lines = [f"# Снимок тендеров", "",
             f"Снято: {snap['снято']} (МСК). Источник: {snap['источник']}.", "",
             f"Всего закупок: **{len(T)}**. Подача заявок открыта (stage=1), окончание не раньше "
             f"{DEADLINE_MSK:%d.%m.%Y %H:%M} МСК, опубликованы за последние {PUBLISHED_DAYS} дней.", "",
             "## По нишам и законам", "", "| Ниша | 44-ФЗ | 223-ФЗ | Всего | С позициями |", "|---|---|---|---|---|"]
    for n in snap["ниши"]:
        s = [t for t in T if t["ниша"] == n]
        lines.append(f"| {n} | {sum(t['закон']=='44-ФЗ' for t in s)} | {sum(t['закон']=='223-ФЗ' for t in s)} | {len(s)} | {sum(bool(t['позиции']) for t in s)} |")
    lines.append(f"| **Итого** | {sum(t['закон']=='44-ФЗ' for t in T)} | {sum(t['закон']=='223-ФЗ' for t in T)} | {len(T)} | {sum(bool(t['позиции']) for t in T)} |")
    ch = sum(len(p['характеристики']) for t in T for p in (t['позиции'] or []))
    pos = sum(len(t['позиции'] or []) for t in T)
    lines += ["", f"Позиций разобрано: {pos}, характеристик: {ch}.", "",
              f"Тип: поставка {sum(t['тип']=='поставка' for t in T)}, смешанная (с флагом) {sum(t['тип']=='смешанная' for t in T)}.",
              f"Закупок с флагом «возможно под конкретного поставщика»: {sum('возможно под конкретного поставщика' in t['флаги'] for t in T)}.", "",
              "## Отсев", ""]
    for k, v in extra["отсев"].items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## Ограничения", "",
              "- Время в API хранится в UTC; в снимке оно переведено в московское. Окончание подачи показано по Москве, "
              "независимо от часового пояса заказчика.",
              f"- Извещения (позиции и характеристики) скачаны только для 44-ФЗ с НМЦ от {NOTICE_NMC[0]:,} до {NOTICE_NMC[1]:,} ₽, "
              f"не больше {NOTICE_PER_NICHE} на нишу, сначала закупки с КТРУ. У остальных 44-ФЗ «позиции» = null.".replace(",", " "),
              "- У 223-ФЗ структурных позиций нет: «позиции» = null, пометка «ТЗ в документах закупки».",
              "- Название заказчика и обеспечение заявки есть только у закупок с загруженным извещением; у остальных "
              "заказчик = null (в списке API только ИНН), обеспечение заявки = null. Обеспечение контракта (%) берётся из списка.",
              "- Не у всех закупок обеспечение контракта задано в процентах: если указана сумма, она в поле «обеспечение_контракта_сумма».",
              f"- Потолок {MAX_PER_NICHE} закупок на нишу (чередование 44-ФЗ/223-ФЗ, свежие первыми), чтобы ниши были сопоставимы.",
              "- Ниша определяется по большинству кодов ОКПД2/КТРУ закупки; многолотовая закупка относится к одной нише.",
              "- Тип и флаги определены только по названию (фильтр_закупок.py), это подсказка, а не вердикт.",
              "- Личные данные (ФИО, телефоны, почты контактных лиц) не сохраняются.",
              "- Ссылка 44-ФЗ взята из извещения, либо собрана по формату ЕИС; для 223-ФЗ и нестандартных способов это поиск ЕИС по номеру.",
              "- Байконур (код 99) в таблице регионов оставлен как 90-я запись; в субъекты РФ он не входит.", ""]
    (DATA / "СНИМОК.md").write_text("\n".join(lines), "utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--без-извещений", dest="noext", action="store_true")
    ap.add_argument("--заново", action="store_true", help="не использовать кэш извещений")
    a = ap.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    now_utc = datetime.now(timezone.utc)
    now_msk = datetime.now(MSK)
    regs = regions_table()
    (DATA / "регионы.json").write_text(json.dumps(regs, ensure_ascii=False, indent=1), "utf-8")

    tenders = collect(now_utc)
    if not tenders:
        die("список закупок пуст — файлы не перезаписаны")
    before = Counter(t["ниша"] for t in tenders)
    tenders = balance(tenders)
    log("по нишам до/после потолка:", {n: (before[n], sum(t['ниша'] == n for t in tenders)) for n in NICHES})
    stat_off = {"всего после отсева работ/услуг и потолка": len(tenders)}
    snap_path = DATA / "снимок.json"
    write_snapshot(tenders, regs, 0, now_msk)

    sel = [] if a.noext else choose_for_notice(tenders)
    log(f"извещений к загрузке: {len(sel)} (~{len(sel) * GAP / 60:.0f} мин)")
    byn = {t["номер"]: t for t in tenders}
    for i, t in enumerate(sel, 1):
        res = get_notice(t, a.заново)
        if res:
            for k in ("заказчик", "способ", "ссылка", "обеспечение_заявки_проц", "обеспечение_контракта_проц"):
                if res.get(k) is not None:
                    t[k] = res[k]
            if res["позиции"]:
                t["позиции"] = res["позиции"]
            else:
                t["позиции_пометка"] = "позиции в извещении не найдены"
        else:
            t["позиции_пометка"] = "извещение недоступно"
        if i % 20 == 0 or i == len(sel):
            log(f"извещение {i}/{len(sel)}")
            write_snapshot(tenders, regs, i, now_msk)
    for t in tenders:
        if t["закон"] == "44-ФЗ" and t["позиции"] is None and "позиции_пометка" not in t:
            t["позиции_пометка"] = "извещение не загружалось (вне приоритета по НМЦ/квоте)"
    snap = write_snapshot(tenders, regs, len(sel), now_msk)
    # отсев пересчитываем из лога коллектора не будем: берём то, что напечатано выше
    write_report(snap, {"отсев": getattr(collect, "stat", stat_off)})
    log("готово:", snap_path, len(snap["тендеры"]), "закупок")


if __name__ == "__main__":
    main()
