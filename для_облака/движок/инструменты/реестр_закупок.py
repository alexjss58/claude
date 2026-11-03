"""Реестр реальных закупок во вход/: номер, заказчик, предмет, ссылка, откуда взят текст, полнота.

Запуск: python инструменты/реестр_закупок.py  ->  вход/реестр_закупок.csv и .md
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tz_engine.eis import parse_notice_file  # noqa: E402

REF = {"0272100000426000191", "0176100004326000053", "32616496528", "0373100099326000008", "0252100003826000222"}
GOLD = {"0813500000126020952", "0340100010926000063", "0373200589126000121", "0252100003826000222", "0820500000826005372"}


def main() -> None:
    rows = []
    files = sorted((ROOT / "вход" / "eis").glob("*.json")) + sorted((ROOT / "вход" / "eis_xml").glob("*.xml")) \
        + sorted((ROOT / "вход" / "eis_отложенная_проверка").glob("*.json"))
    for f in files:
        p = parse_notice_file(f)
        npos = len(p.positions)
        nchar = sum(len(x.requirements) for x in p.positions)
        empty = sum(1 for x in p.positions if not x.requirements)
        if f.suffix == ".xml":
            src = "XML-извещение ЕИС, копия на GitHub (SnootyRoom/B2B_Hackaton, data/samples), скачано через raw.githubusercontent.com"
            api = f"https://raw.githubusercontent.com/SnootyRoom/B2B_Hackaton/HEAD/data/samples/{f.name}"
        else:
            src = "структурированное извещение ЕИС, скачано через открытое API ГосПлан (v2test.gosplan.info)"
            api = f"https://v2test.gosplan.info/{'fz223' if p.law == '223-ФЗ' else 'fz44'}/purchases/{p.number}"
        if empty == npos:
            full = "частично: характеристик в извещении нет (они только в файле ТЗ, который не скачан)"
        elif empty:
            full = f"частично: у {empty} из {npos} позиций характеристик в извещении нет"
        else:
            full = "полностью по извещению (позиции, КТРУ, количество, характеристики с условиями); docx ТЗ не скачан"
        rows.append({
            "номер": p.number, "закон": p.law, "предмет": p.subject, "заказчик": p.customer, "регион": p.region,
            "нмц": p.nmc, "позиций": npos, "характеристик": nchar,
            "откуда_текст": src, "полнота": full, "ссылка_ЕИС": p.url, "ссылка_источник": api,
            "опорная_из_файла_Excel": "да" if p.number in REF else "",
            "в_эталоне": "да" if p.number in GOLD else ("отложенная проверка" if "отложенная" in str(f) else ""),
        })
    out = ROOT / "вход" / "реестр_закупок.csv"
    with open(out, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    md = ["# Реальные закупки, на которых проверен движок", "",
          "Все данные — из ЕИС (zakupki.gov.ru) через открытые копии; сам сайт ЕИС из облака закрыт. "
          "Контакты сотрудников заказчиков из файлов удалены.", "",
          "| № | Номер | Закон | Предмет | Заказчик | Регион | НМЦ, ₽ | Позиций | Характеристик | Полнота | Опорная | Эталон |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        nmc = f"{r['нмц']:,.0f}".replace(",", " ") if r["нмц"] else ""
        md.append(f"| {i} | [{r['номер']}]({r['ссылка_ЕИС']}) | {r['закон']} | {r['предмет'][:80]} | {r['заказчик'][:60]} | "
                  f"{r['регион']} | {nmc} | {r['позиций']} | {r['характеристик']} | {r['полнота'].split(':')[0]} | "
                  f"{r['опорная_из_файла_Excel']} | {r['в_эталоне']} |")
    md += ["", "Источник каждой строки (API ГосПлан или копия XML) — в `реестр_закупок.csv`, столбец «ссылка_источник»."]
    (ROOT / "вход" / "реестр_закупок.md").write_text("\n".join(md) + "\n", "utf-8")
    print(f"закупок: {len(rows)} -> {out.name}, реестр_закупок.md")


if __name__ == "__main__":
    main()
