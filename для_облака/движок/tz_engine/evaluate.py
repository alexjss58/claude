"""Оценка точности: разбор (позиции, характеристики, условия) и сверка — против ручного эталона.

Запуск:  python -m tz_engine.evaluate            (из папки движок/)
Пишет:   эталон/результат_оценки.json и эталон/результат_оценки.md

Маршруты разбора:
  ЕИС-json — структурированное извещение (основной маршрут для 44-ФЗ);
  docx/pdf/xlsx «таблица», txt/docx «текст» — реконструкции документа (см. инструменты/сделать_документы.py).
Дополнительно: согласие текстового разбора со структурированным на всех закупках (автоматически, без эталона).
"""
from __future__ import annotations

import difflib
import json
import re
import time
from pathlib import Path

from .catalog import Catalog
from .eis import parse_notice_file
from .matcher import match_purchase
from .models import Purchase
from .output import req_value
from .readers import read_document
from .text_parser import parse_doc
from .units import lookup, pretty_unit

ROOT = Path(__file__).resolve().parents[1]
GOLD_DIR = ROOT / "эталон"
DOCS = ROOT / "вход" / "документы_реконструкция"


def nn(s: str) -> str:
    s = (s or "").lower().replace("ё", "е").replace(" ", " ")
    s = re.sub(r"[«»\"']", "", s)
    return re.sub(r"\s+", " ", s).strip(" .;:")


def nval(s: str) -> str:
    s = nn(s).replace(",", ".").replace("х", "x").replace("×", "x").replace(" – ", "–").replace("-", "–") \
        .replace("—", "–").replace(" ", "")
    parts = sorted(p for p in re.split(r"[+;/]", s) if p)
    return "|".join(parts)


def nunit(u: str) -> str:
    if not u:
        return ""
    lk = lookup(u)
    return f"{lk[0]}:{lk[1]}" if lk else nn(u)


def gold_purchase(path: Path) -> dict:
    return json.loads(path.read_text("utf-8"))


def _pos_pairs(gold_pos: list, got: Purchase) -> list[tuple[dict, object]]:
    pairs, used = [], set()
    for gp in gold_pos:
        best, bs = None, 0.0
        for j, p in enumerate(got.positions):
            if j in used:
                continue
            s = difflib.SequenceMatcher(None, nn(gp["наименование"]), nn(p.name)).ratio()
            if gp.get("ктру") and p.ktru == gp["ктру"]:
                s += 1
            if s > bs:
                best, bs = j, s
        if best is not None and bs >= 0.6:
            used.add(best)
            pairs.append((gp, got.positions[best]))
        else:
            pairs.append((gp, None))
    return pairs


def score_parse(gold: dict, got: Purchase) -> dict:
    st = {"позиций_эталон": len(gold["позиции"]), "позиций_найдено": len(got.positions), "позиций_совпало": 0,
          "кол-во_верно": 0, "ктру_верно": 0, "хар_эталон": 0, "хар_найдено": 0, "хар_совпало_по_имени": 0,
          "условие_верно": 0, "значение_верно": 0, "единица_верна": 0, "полностью_верно": 0, "ошибки": []}
    for gp, p in _pos_pairs(gold["позиции"], got):
        st["хар_эталон"] += len(gp["характеристики"])
        if p is None:
            st["ошибки"].append(f"позиция «{gp['наименование']}» не найдена")
            continue
        st["позиций_совпало"] += 1
        st["хар_найдено"] += len(p.requirements)
        if p.quantity is not None and abs(float(p.quantity) - float(gp.get("количество") or 0)) < 1e-6:
            st["кол-во_верно"] += 1
        if (p.ktru or "") == (gp.get("ктру") or ""):
            st["ктру_верно"] += 1
        got_by_name = {}
        for r in p.requirements:
            got_by_name.setdefault(nn(r.name), r)
        for name, op, val, unit in gp["характеристики"]:
            r = got_by_name.get(nn(name))
            if r is None:
                m = difflib.get_close_matches(nn(name), list(got_by_name), n=1, cutoff=0.85)
                r = got_by_name.get(m[0]) if m else None
            if r is None:
                st["ошибки"].append(f"[{gp['наименование']}] не найдена характеристика «{name}»")
                continue
            st["хар_совпало_по_имени"] += 1
            op_ok = r.op == op or (op == "=" and r.op == "текст" and False)
            gv = req_value(r)
            val_ok = nval(gv) == nval(val)
            u_got = pretty_unit(r.unit) if r.unit != "пиксель" else "пиксель"
            unit_ok = nunit(u_got) == nunit(unit) or (not unit and not u_got) or (unit == "пиксель" and r.unit == "пиксель")
            st["условие_верно"] += op_ok
            st["значение_верно"] += val_ok
            st["единица_верна"] += unit_ok
            if op_ok and val_ok and unit_ok:
                st["полностью_верно"] += 1
            else:
                bad = []
                if not op_ok:
                    bad.append(f"условие {r.op} вместо {op}")
                if not val_ok:
                    bad.append(f"значение «{gv}» вместо «{val}»")
                if not unit_ok:
                    bad.append(f"единица «{u_got}» вместо «{unit}»")
                st["ошибки"].append(f"[{gp['наименование']}] {name}: " + "; ".join(bad))
    return st


def score_match(gold: dict, got: Purchase, results) -> dict:
    st = {"позиций": 0, "статус_верно": 0, "товар_верно": 0, "товар_оценивался": 0, "ошибки": []}
    for gp, p in _pos_pairs(gold["позиции"], got):
        exp = gp.get("ожидаемая_сверка") or {}
        if p is None or not exp:
            continue
        st["позиций"] += 1
        m = results[got.positions.index(p)]
        if m.status == exp["статус"]:
            st["статус_верно"] += 1
        else:
            st["ошибки"].append(f"[{gp['наименование']}] статус «{m.status}» вместо «{exp['статус']}» ({m.reason})")
        if exp.get("подходящие_товары"):
            st["товар_оценивался"] += 1
            sku = (m.product or {}).get("_sku", "")
            if sku in exp["подходящие_товары"]:
                st["товар_верно"] += 1
            else:
                st["ошибки"].append(f"[{gp['наименование']}] выбран «{sku}», ожидался один из {exp['подходящие_товары']}")
    return st


def _sum(dicts: list[dict]) -> dict:
    out: dict = {}
    for d in dicts:
        for k, v in d.items():
            if isinstance(v, (int, float)):
                out[k] = out.get(k, 0) + v
            elif isinstance(v, list):
                out.setdefault(k, []).extend(v)
    return out


def pct(a, b) -> str:
    return f"{100 * a / b:.0f}%" if b else "—"


def reference_to_gold(p: Purchase) -> dict:
    """Структурированный разбор как «эталон» для автоматической проверки текстового разбора."""
    return {"позиции": [{"наименование": x.name, "ктру": x.ktru, "количество": x.quantity,
                         "характеристики": [[r.name, r.op, req_value(r), pretty_unit(r.unit) if r.unit != "пиксель" else "пиксель"]
                                            for r in x.requirements]} for x in p.positions]}


ROUTES = [("ЕИС-json", None), ("docx-таблица", "_таблица.docx"), ("pdf-таблица", "_таблица.pdf"),
          ("xlsx-таблица", "_таблица.xlsx"), ("txt-текст", "_текст.txt"), ("docx-текст", "_текст.docx")]


def run() -> dict:
    cat = Catalog.load(ROOT / "каталог_демо.xlsx")
    golds = sorted(GOLD_DIR.glob("0*.json"))
    report: dict = {"разбор": {}, "сверка": {}, "время_с": {}, "согласие_текст_со_структурой": {}}
    for route, suffix in ROUTES:
        per, times = [], []
        for g in golds:
            gold = gold_purchase(g)
            num = gold["номер"]
            t0 = time.perf_counter()
            if suffix is None:
                got = parse_notice_file(ROOT / "вход" / "eis" / f"{num}.json")
            else:
                f = DOCS / f"{num}{suffix}"
                if not f.exists():
                    continue
                got = parse_doc(read_document(f))
            times.append(time.perf_counter() - t0)
            per.append(score_parse(gold, got))
            if suffix in (None, "_таблица.docx"):
                t1 = time.perf_counter()
                res = match_purchase(got, cat)
                times[-1] += time.perf_counter() - t1
                report["сверка"].setdefault(route, []).append(score_match(gold, got, res))
        report["разбор"][route] = _sum(per)
        report["время_с"][route] = round(sum(times) / max(1, len(times)), 4)
    # отложенная проверка сверки: закупки, которые движок не видел при отладке
    hold = []
    for g in sorted((GOLD_DIR / "отложенная_проверка").glob("*.json")):
        gold = gold_purchase(g)
        got = parse_notice_file(ROOT / "вход" / "eis_отложенная_проверка" / f"{gold['номер']}.json")
        hold.append(score_match(gold, got, match_purchase(got, cat)))
    if hold:
        report["сверка"]["отложенная проверка (новые закупки)"] = hold
    for route in list(report["сверка"]):
        report["сверка"][route] = _sum(report["сверка"][route])
    # согласие на всех закупках
    for route, suffix in ROUTES[1:]:
        per = []
        for f in sorted(DOCS.glob(f"*{suffix}")):
            num = f.name.split("_")[0]
            ref = parse_notice_file(ROOT / "вход" / "eis" / f"{num}.json")
            if not ref.positions:
                continue
            per.append(score_parse(reference_to_gold(ref), parse_doc(read_document(f))))
        if per:
            s = _sum(per)
            s["закупок"] = len(per)
            s["ошибки"] = s.get("ошибки", [])[:40]
            report["согласие_текст_со_структурой"][route] = s
    return report


def to_markdown(rep: dict) -> str:
    L = ["| Маршрут | Позиции найдены | Характеристики найдены (полнота) | Лишние | Условие верно | Значение верно | Единица верна | Полностью верно | Кол-во верно | КТРУ верно | Секунд на закупку |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for route, s in rep["разбор"].items():
        if not s:
            continue
        m = s.get("хар_совпало_по_имени", 0)
        extra = max(0, s.get("хар_найдено", 0) - m)
        L.append(f"| {route} | {s['позиций_совпало']}/{s['позиций_эталон']} | {m}/{s['хар_эталон']} ({pct(m, s['хар_эталон'])}) | {extra} | "
                 f"{pct(s['условие_верно'], m)} | {pct(s['значение_верно'], m)} | {pct(s['единица_верна'], m)} | "
                 f"{s['полностью_верно']}/{s['хар_эталон']} ({pct(s['полностью_верно'], s['хар_эталон'])}) | "
                 f"{s['кол-во_верно']}/{s['позиций_совпало']} | {s['ктру_верно']}/{s['позиций_совпало']} | {rep['время_с'].get(route, 0)} |")
    L += ["", "| Маршрут | Статус сверки верно | Товар выбран верно |", "|---|---|---|"]
    for route, s in rep["сверка"].items():
        L.append(f"| {route} | {s['статус_верно']}/{s['позиций']} ({pct(s['статус_верно'], s['позиций'])}) | "
                 f"{s['товар_верно']}/{s['товар_оценивался']} ({pct(s['товар_верно'], s['товар_оценивался'])}) |")
    L += ["", "Согласие текстового разбора со структурированным извещением (все закупки с позициями, без ручного эталона):", "",
          "| Маршрут | Закупок | Характеристики найдены | Полностью верно |", "|---|---|---|---|"]
    for route, s in rep["согласие_текст_со_структурой"].items():
        L.append(f"| {route} | {s['закупок']} | {s['хар_совпало_по_имени']}/{s['хар_эталон']} ({pct(s['хар_совпало_по_имени'], s['хар_эталон'])}) | "
                 f"{s['полностью_верно']}/{s['хар_эталон']} ({pct(s['полностью_верно'], s['хар_эталон'])}) |")
    return "\n".join(L)


def main() -> None:
    rep = run()
    (GOLD_DIR / "результат_оценки.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), "utf-8")
    md = to_markdown(rep)
    (GOLD_DIR / "результат_оценки.md").write_text(md + "\n", "utf-8")
    print(md)
    print()
    for route, s in rep["разбор"].items():
        if s.get("ошибки"):
            print(f"--- ошибки разбора, {route} (первые 15):")
            for e in s["ошибки"][:15]:
                print("   ", e)
    for route, s in rep["сверка"].items():
        if s.get("ошибки"):
            print(f"--- ошибки сверки, {route}:")
            for e in s["ошибки"]:
                print("   ", e)


if __name__ == "__main__":
    main()
