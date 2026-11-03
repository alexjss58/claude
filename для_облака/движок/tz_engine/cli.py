"""Командная строка движка сверки.

Примеры (из папки для_облака/):
    python -m движок.сверка движок/вход/eis/0813500000126020952.json --каталог движок/каталог_демо.xlsx
    python -m движок.сверка движок/вход/ --каталог мой_прайс.xlsx --выход движок/демо_выход
или из папки движок/:
    python -m tz_engine вход/eis --каталог каталог_демо.xlsx

Режимы разбора текста: --режим авто (по умолчанию: Claude API, если задан ANTHROPIC_API_KEY, иначе правила),
--режим правила, --режим claude. Извещения ЕИС (json/xml) всегда разбираются напрямую — модель там не нужна.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path

from . import llm
from .catalog import Catalog
from .eis import looks_like_notice, parse_notice_file
from .matcher import match_purchase
from .output import to_f, to_markdown
from .readers import SUPPORTED, read_document
from .text_parser import parse_doc

ROOT = Path(__file__).resolve().parents[1]


def collect(paths: list[str]) -> list[Path]:
    out = []
    for p in paths:
        pp = Path(p)
        if pp.is_dir():
            for f in sorted(pp.rglob("*")):
                if f.is_file() and (f.suffix.lower() in SUPPORTED or f.suffix.lower() in (".json", ".xml")) \
                        and not f.name.startswith(("~", ".")):
                    out.append(f)
        elif pp.exists():
            out.append(pp)
        else:
            print(f"нет такого файла: {p}", file=sys.stderr)
    return out


def process(path: Path, catalog: Catalog, mode: str) -> tuple[dict, dict]:
    t0 = time.perf_counter()
    info: dict = {"файл": str(path)}
    if looks_like_notice(path):
        pur = parse_notice_file(path)
        f_mode = "демо"
    else:
        doc = read_document(path)
        use_llm = mode == "claude" or (mode == "авто" and llm.available())
        if use_llm:
            pur, call = llm.parse_text(doc.text())
            info.update(call)
            f_mode = "живой"
        else:
            pur = parse_doc(doc)
            f_mode = "демо"
            info["оценка_claude"] = llm.estimate_cost(doc.text())
        if not pur.number:
            m = re.search(r"(0\d{18}|3\d{10})", path.stem)
            if m:
                pur.number = m.group(1)
        pur.source = f"файл {path.name} (" + ("Claude API" if use_llm else "правила + регулярные выражения") + ")"
        if "РЕКОНСТРУКЦИЯ" in doc.text()[:300]:
            pur.source += "; реконструкция документа из извещения ЕИС, не скачан с ЕИС"
    results = match_purchase(pur, catalog)
    out = to_f(pur, results, mode=f_mode)
    info["секунд"] = round(time.perf_counter() - t0, 3) if "секунд" not in info else info["секунд"]
    info["разбор"] = pur.parser
    return out, info


def print_human(out: dict) -> None:
    z = out["закупка"]
    print(f"\n=== {z['номер'] or '(без номера)'} — {z['предмет'][:90]}")
    if z.get("заказчик"):
        print(f"    заказчик: {z['заказчик'][:90]}")
    for p in out["позиции"]:
        s = p["сверка"]
        mark = {"подходит": "[+]", "почти": "[~]", "нет": "[-]"}[s["статус"]]
        print(f"  {mark} {p['№']}. {p['наименование'][:60]} — {p['количество']} {p['единица']}: {s['статус']}"
              + (f" → {s['товар_из_каталога'][:60]}" if s["товар_из_каталога"] else ""))
        for r in s["расхождения"][:4]:
            print(f"        • {r['характеристика'][:60]}: нужно {r['требуется']}, у товара {r['у_товара'][:50]}")
        if len(s["расхождения"]) > 4:
            print(f"        … ещё {len(s['расхождения']) - 4}")
    print(f"  итог: {out['итог']}")


def write_summary(rows: list[dict], outdir: Path) -> None:
    if not rows:
        return
    keys = list(rows[0].keys())
    with open(outdir / "сводка.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    try:
        import pandas as pd
        pd.DataFrame(rows).to_excel(outdir / "сводка.xlsx", index=False)
    except Exception:
        pass
    index = [{"номер": r["номер"], "предмет": r["предмет"], "заказчик": r["заказчик"], "регион": r["регион"], "нмц": r["нмц"],
              "итог": {"подходит": r["подходит"], "почти": r["почти"], "нет": r["нет"]}, "файл": f"{r['номер']}.json"}
             for r in rows if r.get("номер")]
    (outdir / "индекс.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), "utf-8")
    md = ["| " + " | ".join(keys) + " |", "|" + "---|" * len(keys)]
    for r in rows:
        md.append("| " + " | ".join(str(r[k]).replace("|", "/") for k in keys) + " |")
    (outdir / "сводка.md").write_text("\n".join(md) + "\n", "utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="сверка", description="Сверка техзадания с каталогом поставщика")
    ap.add_argument("документы", nargs="+", help="файлы или папки: извещение ЕИС (json/xml), docx, pdf, xlsx, txt")
    ap.add_argument("--каталог", default=str(ROOT / "каталог_демо.xlsx"), help="каталог поставщика (xlsx/csv)")
    ap.add_argument("--выход", default=None, help="папка для JSON (по умолчанию движок/демо_выход)")
    ap.add_argument("--режим", default="авто", choices=["авто", "правила", "claude"])
    ap.add_argument("--тихо", action="store_true", help="не печатать подробности")
    ap.add_argument("--столбцы", action="store_true", help="показать, как распознаны столбцы каталога")
    a = ap.parse_args(argv)

    catalog = Catalog.load(a.каталог)
    if a.столбцы:
        for col, key in catalog.columns_report():
            print(f"  {col} -> {key}")
    outdir = Path(a.выход) if a.выход else ROOT / "демо_выход"
    outdir.mkdir(parents=True, exist_ok=True)
    files = collect(a.документы)
    if not files:
        print("нечего обрабатывать", file=sys.stderr)
        return 1
    rows = []
    for f in files:
        try:
            out, info = process(f, catalog, a.режим)
        except Exception as e:  # один плохой файл не должен ронять пакет
            print(f"ошибка в {f}: {e}", file=sys.stderr)
            continue
        z = out["закупка"]
        name = z["номер"] or f.stem
        (outdir / f"{name}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), "utf-8")
        (outdir / "читать").mkdir(exist_ok=True)
        (outdir / "читать" / f"{name}.md").write_text(to_markdown(out), "utf-8")
        if not a.тихо:
            print_human(out)
        rows.append({"номер": z["номер"], "закон": z["закон"], "предмет": z["предмет"][:120], "заказчик": z["заказчик"][:80],
                     "регион": z["регион"], "нмц": z["нмц"], "позиций": len(out["позиции"]),
                     "характеристик": sum(len(p["характеристики"]) for p in out["позиции"]),
                     "подходит": out["итог"]["подходит"], "почти": out["итог"]["почти"], "нет": out["итог"]["нет"],
                     "разбор": info.get("разбор", ""), "секунд": info.get("секунд", ""),
                     "источник": z["источник_документа"][:140], "ссылка": z["ссылка"]})
    write_summary(rows, outdir)
    print(f"\nготово: {len(rows)} закупок -> {outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
