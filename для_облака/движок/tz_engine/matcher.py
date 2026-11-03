"""Сверка позиций техзадания с каталогом поставщика.

Для каждой позиции:
1) определяем категорию (по названию, КТРУ/ОКПД2);
2) берём все товары каталога этой категории;
3) у каждого товара проверяем каждую характеристику: ok / fail / нет данных / нет в каталоге;
4) лучший товар — с наименьшим числом несоответствий, затем «нет данных», затем больше совпадений.

Статус:
* «подходит» — несоответствий нет, по всем сопоставленным характеристикам данные есть,
  сопоставлено не меньше половины характеристик. Остальные (комплектация, габариты и т. п.)
  идут в список «проверить» — их каталог не описывает.
* «почти» — 1–2 несоответствия ИЛИ нет данных в каталоге по части характеристик
  (тогда «у_товара» = «нет данных в каталоге»);
* «нет» — в каталоге нет товаров этой категории или у лучшего товара 3+ несоответствия.
"""
from __future__ import annotations

import re

from .catalog import Catalog
from .conditions import compare, numbers_in, text_match
from .models import Check, MatchResult, Position
from .synonyms import detect_category, is_kit, map_key

MAX_FAILS_ALMOST = 2
# Параметры, которые меняются выбором другой конфигурации той же модели (или опцией).
# Несоответствие по ним — «почти»; по остальным (цветность, формат, диагональ, порты, PoE…) — «нет».
CONFIGURABLE = {"ram", "ram_type", "ssd", "hdd", "storage_type", "storage_if", "os", "psu", "cpu", "cpu_base", "cpu_max",
                "cpu_cores", "cpu_threads", "cpu_l3", "cpu_tdp", "gpu", "gpu_discrete", "gpu_integrated", "wifi",
                "bluetooth", "fax", "hs_type", "lan_speed", "webcam", "kb_backlight"}
# для текстового сравнения берём ещё соседние столбцы (Wi-Fi и Bluetooth часто записаны отдельно)
EXTRA = {"wifi": ["bluetooth"], "ports_text": ["wifi", "bluetooth", "video_inputs", "storage_type", "storage_if"],
         "connection": ["wifi"], "video_inputs": ["ports_text"]}
# если в своём столбце пусто, а требование «есть/нет», ищем упоминание в текстовых столбцах
TEXT_FALLBACK = {"usb_any": "usb", "usb2": "usb 2", "usb3": "usb 3", "usb_c": "type-c", "hdmi": "hdmi", "dp": "displayport",
                 "vga": "vga", "rj45": "rj-45", "network": "ethernet", "wifi": "wi-fi", "bluetooth": "bluetooth"}
TEXT_COLS = ["connection", "ports_text", "video_inputs", "wifi", "bluetooth"]
# «закрытые перечни»: в каталоге перечислены все порты/интерфейсы — отсутствие значит «нет»
CLOSED = {"video_inputs", "ports_text", "connection", "hs_connection", "wifi"}
MIN_MAPPED_SHARE = 0.5


def refine_category(pos: Position) -> str | None:
    cat = pos.category or detect_category(pos.name, pos.ktru, pos.okpd2)
    if cat == "телефон":
        blob = " ".join(f"{r.name} {r.value} {' '.join(r.values)}" for r in pos.requirements).lower()
        if re.search(r"\bsip\b|\bip\b|voip|ethernet|poe", blob):
            cat = "ip-телефон"
    pos.category = cat
    return cat


def check_product(pos: Position, prod: dict, cat: str) -> list[Check]:
    out = []
    for req in pos.requirements:
        k = map_key(req.name, cat)
        if k is None:
            out.append(Check(req, "unmapped", "комплектация — в каталоге не описывается" if is_kit(req.name) else ""))
            continue
        req.key = k.key
        val = prod.get(k.key)
        if val is None and k.key == "uplink":
            # uplink-порты = SFP+/SFP/комбо (что есть у модели)
            nums = [n for x in ("ports_sfp10", "ports_sfp", "ports_combo") for n in numbers_in(prod.get(x, ""))]
            val = f"{int(max(nums))} (по SFP/SFP+/комбо)" if nums and max(nums) > 0 else None
        if k.kind == "text" and k.key in EXTRA:
            parts = [val] + [prod.get(x) for x in EXTRA[k.key]]
            parts = [x for x in parts if x]
            val = " | ".join(parts) if parts else None
        unit = prod.get("_units", {}).get(k.key) or k.unit
        st, have = compare(req, val, unit, kind=k.kind, key=k.key, closed=k.key in CLOSED)
        presence = req.values in (["да"], ["нет"]) or (req.op == ">=" and req.vmin is not None and req.vmin <= 1)
        if st == "unknown" and not val and k.key in TEXT_FALLBACK and presence:
            blob = " | ".join(prod.get(c, "") for c in TEXT_COLS if prod.get(c))
            if blob and text_match(blob, TEXT_FALLBACK[k.key]) == "ok":
                st, have = ("fail" if req.values == ["нет"] else "ok"), "есть в описании: " + blob[:80]
        out.append(Check(req, st, have))
    return out


def product_title(prod: dict) -> str:
    t = f"{prod.get('_vendor', '')} {prod.get('_model', '')}".strip()
    return t


def match_position(pos: Position, catalog: Catalog) -> MatchResult:
    cat = refine_category(pos)
    if not cat:
        return MatchResult("нет", None, [Check(r, "unmapped") for r in pos.requirements],
                           reason="категория товара не распознана — в каталоге такого нет")
    cands = catalog.by_category(cat)
    if not cands:
        return MatchResult("нет", None, [Check(r, "unmapped") for r in pos.requirements],
                           reason=f"в каталоге нет товаров категории «{cat}»")
    scored = []
    for prod in cands:
        checks = check_product(pos, prod, cat)
        f = sum(c.status == "fail" for c in checks)
        hard = sum(c.status == "fail" and c.req.key not in CONFIGURABLE for c in checks)
        u = sum(c.status == "unknown" for c in checks)
        ok = sum(c.status == "ok" for c in checks)
        scored.append(((hard, f, u, -ok), prod, checks))
    scored.sort(key=lambda x: x[0])
    (hard, f, u, nok), prod, checks = scored[0]
    total = len(pos.requirements)
    mapped = sum(c.status != "unmapped" for c in checks)
    if total == 0:
        return MatchResult("почти", prod, checks,
                           reason="в извещении нет характеристик позиции — сверить по файлу техзадания")
    if hard > 0:
        names = ", ".join(c.req.name for c in checks if c.status == "fail" and c.req.key not in CONFIGURABLE)[:200]
        return MatchResult("нет", prod, checks, reason=f"ближайший товар не проходит по неизменяемым характеристикам: {names}")
    if f > MAX_FAILS_ALMOST:
        return MatchResult("нет", prod, checks, reason=f"ближайший товар не проходит по {f} характеристикам")
    if f > 0:
        return MatchResult("почти", prod, checks, reason=f"не проходит по {f} характеристикам, которые меняются конфигурацией (память, накопитель, процессор и т. п.)")
    if u > 0:
        return MatchResult("почти", prod, checks, reason=f"в каталоге нет данных по {u} характеристикам")
    if mapped / total < MIN_MAPPED_SHARE:
        return MatchResult("почти", prod, checks,
                           reason=f"каталог описывает только {mapped} из {total} характеристик — проверить по паспорту")
    return MatchResult("подходит", prod, checks, reason="все сопоставленные характеристики совпали")


def match_purchase(pur, catalog: Catalog) -> list[MatchResult]:
    return [match_position(p, catalog) for p in pur.positions]
