"""Собрать документы «Описание объекта закупки» из структурированных извещений ЕИС — для проверки текстового разбора.

ВАЖНО. Это РЕКОНСТРУКЦИЯ, а не скачанный с ЕИС файл: zakupki.gov.ru из облака закрыт,
поэтому настоящий docx заказчика получить нельзя. Данные (позиции, характеристики, условия)
настоящие — из извещения; оформление сделано движком в двух типичных видах:
  * «таблица» — как печатная форма ЕИС / большинство заказчиков (docx, pdf, xlsx);
  * «текст» — свободный текст «Характеристика: не менее 16 ГБ» (txt, docx).
В каждом документе первой строкой написано, что это реконструкция.

Запуск:  python инструменты/сделать_документы.py [номер ...]
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tz_engine.eis import parse_notice_file  # noqa: E402
from tz_engine.models import Purchase, Requirement, fmt  # noqa: E402
from tz_engine.units import pretty_unit  # noqa: E402

OUT = ROOT / "вход" / "документы_реконструкция"
GOLD = ["0813500000126020952", "0340100010926000063", "0373200589126000121", "0252100003826000222", "0820500000826005372"]
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def note(p: Purchase) -> str:
    return (f"РЕКОНСТРУКЦИЯ для проверки разбора (не скачано с ЕИС): собрано из структурированного извещения ЕИС "
            f"№ {p.number}, данные — из открытого API ГосПлан.")


def unit_s(r: Requirement) -> str:
    return "" if r.unit == "пиксель" else pretty_unit(r.unit)


def table_value(r: Requirement) -> str:
    if r.op == ">=" and r.vmin is not None:
        return ("> " if r.min_strict else "≥ ") + fmt(r.vmin)
    if r.op == "<=" and r.vmax is not None:
        return ("< " if r.max_strict else "≤ ") + fmt(r.vmax)
    if r.op == "диапазон":
        return f"≥ {fmt(r.vmin)} и ≤ {fmt(r.vmax)}"
    if r.op == "=" and r.vmin is not None and not r.values:
        return fmt(r.vmin)
    if r.values and r.unit == "пиксель":
        return ("≥ " if r.op == ">=" else "≤ " if r.op == "<=" else "") + r.values[0]
    if r.values:
        return "; ".join("Да" if v == "да" else "Нет" if v == "нет" else v for v in r.values)
    return r.value or r.raw


def text_value(r: Requirement) -> str:
    u = unit_s(r)
    u = f" {u}" if u else ""
    if r.op == ">=" and r.vmin is not None:
        return ("более " if r.min_strict else "не менее ") + fmt(r.vmin) + u
    if r.op == "<=" and r.vmax is not None:
        return ("менее " if r.max_strict else "не более ") + fmt(r.vmax) + u
    if r.op == "диапазон":
        return f"от {fmt(r.vmin)} до {fmt(r.vmax)}{u}"
    if r.op == "=" and r.vmin is not None and not r.values:
        return fmt(r.vmin) + u
    if r.values and r.unit == "пиксель":
        return ("не менее " if r.op == ">=" else "не более " if r.op == "<=" else "") + r.values[0] + " пикселей"
    if r.values:
        vals = ["наличие" if v == "да" else "отсутствие" if v == "нет" else v for v in r.values]
        return ", ".join(vals) if r.all_values else " или ".join(vals)
    return r.value or r.raw


HEAD = ["№ п/п", "Наименование товара", "Код КТРУ / ОКПД2", "Наименование характеристики", "Значение характеристики",
        "Единица измерения характеристики", "Инструкция по заполнению характеристик в заявке", "Количество", "Ед. изм."]


def table_rows(p: Purchase) -> list[list[str]]:
    rows = []
    for pos in p.positions:
        q = fmt(pos.quantity) if pos.quantity is not None else ""
        first = True
        reqs = pos.requirements or [None]
        for r in reqs:
            rows.append([str(pos.num) if first else "", pos.name if first else "", (pos.ktru or pos.okpd2) if first else "",
                         r.name if r else "", table_value(r) if r else "", unit_s(r) if r else "",
                         r.instruction if r else "", q if first else "", pos.unit if first else ""])
            first = False
    return rows


def make_docx_table(p: Purchase, path: Path) -> None:
    import docx
    d = docx.Document()
    d.add_paragraph(note(p))
    d.add_paragraph("ОПИСАНИЕ ОБЪЕКТА ЗАКУПКИ")
    d.add_paragraph(f"Объект закупки: {p.subject}")
    d.add_paragraph(f"Заказчик: {p.customer}")
    rows = table_rows(p)
    t = d.add_table(rows=1 + len(rows), cols=len(HEAD))
    t.style = "Table Grid"
    for j, h in enumerate(HEAD):
        t.rows[0].cells[j].text = h
    for i, row in enumerate(rows, 1):
        for j, c in enumerate(row):
            t.rows[i].cells[j].text = c
    d.save(str(path))


def make_xlsx(p: Purchase, path: Path) -> None:
    import pandas as pd
    rows = [[note(p)] + [""] * (len(HEAD) - 1), ["ОПИСАНИЕ ОБЪЕКТА ЗАКУПКИ"] + [""] * (len(HEAD) - 1), HEAD] + table_rows(p)
    pd.DataFrame(rows).to_excel(path, header=False, index=False)


def make_pdf(p: Purchase, path: Path) -> None:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

    if "DejaVu" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("DejaVu", FONT))
    st = ParagraphStyle("n", fontName="DejaVu", fontSize=7, leading=8.5)
    big = ParagraphStyle("b", fontName="DejaVu", fontSize=10, leading=12)
    data = [[Paragraph(h, st) for h in HEAD]] + [[Paragraph(c.replace("&", "&amp;").replace("<", "&lt;"), st) for c in row]
                                                 for row in table_rows(p)]
    widths = [22, 80, 75, 150, 150, 50, 110, 40, 35]
    tbl = Table(data, colWidths=widths, repeatRows=1)
    tbl.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.black), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    docpdf = SimpleDocTemplate(str(path), pagesize=landscape(A4), leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
    docpdf.build([Paragraph(note(p), big), Paragraph("ОПИСАНИЕ ОБЪЕКТА ЗАКУПКИ", big),
                  Paragraph(f"Объект закупки: {p.subject}", big), tbl])


def free_text(p: Purchase) -> str:
    lines = [note(p), "", "ТЕХНИЧЕСКОЕ ЗАДАНИЕ (ОПИСАНИЕ ОБЪЕКТА ЗАКУПКИ)", f"Объект закупки: {p.subject}",
             f"Заказчик: {p.customer}", "", "Требования к товару:"]
    for pos in p.positions:
        code = f" (КТРУ {pos.ktru})" if pos.ktru else (f" (ОКПД2 {pos.okpd2})" if pos.okpd2 else "")
        q = f" — {fmt(pos.quantity)} {pos.unit}" if pos.quantity is not None else ""
        lines.append(f"{pos.num}. {pos.name}{q}{code}")
        for r in pos.requirements:
            lines.append(f"{r.name}: {text_value(r)}")
        lines.append("")
    lines += ["Требования к сроку и месту поставки: в соответствии с проектом контракта."]
    return "\n".join(lines)


def make_docx_text(p: Purchase, path: Path) -> None:
    import docx
    d = docx.Document()
    for line in free_text(p).split("\n"):
        d.add_paragraph(line)
    d.save(str(path))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted((ROOT / "вход" / "eis").glob("*.json"))
    only = set(sys.argv[1:])
    n = 0
    for f in files:
        p = parse_notice_file(f)
        if p.law != "44-ФЗ" or not p.positions or (only and p.number not in only):
            continue
        base = OUT / p.number
        make_docx_table(p, base.with_name(f"{p.number}_таблица.docx"))
        (base.with_name(f"{p.number}_текст.txt")).write_text(free_text(p), "utf-8")
        if p.number in GOLD:
            make_pdf(p, base.with_name(f"{p.number}_таблица.pdf"))
            make_xlsx(p, base.with_name(f"{p.number}_таблица.xlsx"))
            make_docx_text(p, base.with_name(f"{p.number}_текст.docx"))
        n += 1
    print("готово документов для закупок:", n, "->", OUT)


if __name__ == "__main__":
    main()
