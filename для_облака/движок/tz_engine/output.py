"""Выход в формате «G → F» (см. ПОТОКИ.md) и сводная таблица.

Обязательные поля формата сохранены как есть. Добавлены только необязательные поля
(их можно не читать): «строго» в характеристике, «проверить» и «причина» в сверке,
«нацрежим_в_извещении» и «разобрано» в закупке.
"""
from __future__ import annotations

import re
from datetime import datetime

from .models import MatchResult, Purchase, Requirement, fmt
from .units import pretty_unit

OP_OUT = {">=": ">=", "<=": "<=", "=": "=", "диапазон": "диапазон", "из_списка": "из_списка", "текст": "текст"}


def _date(s: str) -> str:
    if not s:
        return ""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m.group(3)}.{m.group(2)}.{m.group(1)}"
    return s


def req_value(r: Requirement) -> str:
    if r.op == ">=" and r.vmin is not None:
        return fmt(r.vmin)
    if r.op == "<=" and r.vmax is not None:
        return fmt(r.vmax)
    if r.op == "диапазон":
        return f"{fmt(r.vmin)}–{fmt(r.vmax)}"
    if r.op == "=" and r.vmin is not None and not r.values:
        return fmt(r.vmin)
    if r.values:
        return (" + " if r.all_values else "; ").join(r.values)
    return r.value or r.raw


def req_to_f(r: Requirement) -> dict:
    d = {"имя": r.name, "условие": OP_OUT.get(r.op, "текст"), "значение": req_value(r),
         "единица": pretty_unit(r.unit) if r.unit != "пиксель" else "пиксель",
         "эквивалент_допускается": bool(r.equiv)}
    if r.min_strict or r.max_strict:
        d["строго"] = True
    return d


def match_to_f(m: MatchResult) -> dict:
    prod = m.product or {}
    title = f"{prod.get('_vendor', '')} {prod.get('_model', '')}".strip()
    if prod.get("_config"):
        title += f" ({prod['_config']})"
    rasx = []
    for c in m.checks:
        if c.status == "fail":
            rasx.append({"характеристика": c.req.name, "требуется": c.req.describe(), "у_товара": c.have})
    if m.status != "подходит":
        for c in m.checks:
            if c.status == "unknown":
                rasx.append({"характеристика": c.req.name, "требуется": c.req.describe(),
                             "у_товара": "нет данных в каталоге" + (f" ({c.have})" if c.have else "")})
    check = [c.req.name for c in m.checks if c.status == "unmapped"]
    out = {"статус": m.status, "товар_из_каталога": title if prod else "", "артикул": prod.get("_sku", ""),
           "расхождения": rasx}
    if check:
        out["проверить"] = check
    if m.reason:
        out["причина"] = m.reason
    return out


def to_f(pur: Purchase, results: list[MatchResult], mode: str = "демо") -> dict:
    poss = []
    for pos, m in zip(pur.positions, results):
        poss.append({
            "№": pos.num, "наименование": pos.name, "ктру": pos.ktru, "окпд2": pos.okpd2,
            "количество": (int(pos.quantity) if pos.quantity is not None and float(pos.quantity).is_integer() else pos.quantity) or 0,
            "единица": pos.unit or "шт",
            "характеристики": [req_to_f(r) for r in pos.requirements],
            "сверка": match_to_f(m),
        })
    itog = {"подходит": 0, "почти": 0, "нет": 0}
    for m in results:
        itog[m.status] = itog.get(m.status, 0) + 1
    zak = {"номер": pur.number, "предмет": pur.subject, "заказчик": pur.customer, "инн_заказчика": pur.customer_inn,
           "закон": pur.law, "способ": pur.method, "нмц": pur.nmc or 0, "регион": pur.region,
           "дата_окончания": _date(pur.deadline), "ссылка": pur.url, "источник_документа": pur.source}
    if pur.foreign_restriction is not None:
        zak["нацрежим_в_извещении"] = bool(pur.foreign_restriction)
    zak["разобрано"] = f"{pur.parser}, {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    return {"закупка": zak, "позиции": poss, "итог": itog, "режим": mode}


def to_markdown(out: dict) -> str:
    """Человекочитаемый отчёт по одной закупке (для встречи с тендерщиком)."""
    z = out["закупка"]
    mark = {"подходит": "🟢 подходит", "почти": "🟡 почти", "нет": "🔴 нет"}
    L = [f"# Закупка {z['номер']}", "", f"**{z['предмет']}**", "",
         f"- Заказчик: {z['заказчик']}" + (f" (ИНН {z['инн_заказчика']})" if z.get("инн_заказчика") else ""),
         f"- Закон: {z['закон']}; способ: {z['способ']}; НМЦ: {z['нмц']:,.2f} ₽".replace(",", " ") if z.get("нмц") else f"- Закон: {z['закон']}; способ: {z['способ']}",
         f"- Регион: {z['регион']}; окончание подачи заявок: {z['дата_окончания']}",
         f"- Ссылка: {z['ссылка']}", f"- Откуда данные: {z['источник_документа']}"]
    if z.get("нацрежим_в_извещении"):
        L.append("- В извещении установлены ограничения/запрет на иностранные товары (нацрежим) — проверить реестры.")
    it = out["итог"]
    L += ["", f"**Итог:** подходит — {it['подходит']}, почти — {it['почти']}, нет — {it['нет']}. "
          f"Режим: {out['режим']} (демо = правила, без ИИ).", ""]
    for p in out["позиции"]:
        s = p["сверка"]
        L.append(f"## {p['№']}. {p['наименование']} — {p['количество']} {p['единица']} · {mark.get(s['статус'], s['статус'])}")
        if p.get("ктру"):
            L.append(f"КТРУ {p['ктру']}")
        if s["товар_из_каталога"]:
            L.append(f"Товар из каталога: **{s['товар_из_каталога']}** (артикул {s['артикул']})")
        if s.get("причина"):
            L.append(f"Почему: {s['причина']}")
        if s["расхождения"]:
            L += ["", "| Характеристика | Требуется | У товара |", "|---|---|---|"]
            for r in s["расхождения"]:
                L.append(f"| {r['характеристика']} | {r['требуется']} | {r['у_товара']} |")
        if s.get("проверить"):
            L.append("")
            L.append("Проверить вручную (в каталоге не описывается): " + "; ".join(s["проверить"][:15])
                     + (f" … и ещё {len(s['проверить']) - 15}" if len(s["проверить"]) > 15 else ""))
        L.append("")
    return "\n".join(L)
