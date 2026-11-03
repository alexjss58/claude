"""Добавляет в модель.xlsx лист «Себестоимость по этапам».

Раскладывает полную себестоимость заявки с листа «Юнит-экономика» (колонка G — выбранный сценарий)
по этапам тендера. Всё на формулах: жёлтые ячейки — допущения о том, как ручное время и токены ИИ
делятся между этапами (в данных этого нет, это оценка). Итог листа совпадает с «Юнит-экономика»!G13.

Запуск: python3 add_stage_sheet.py  (build_model.py вызывает его сам в конце).
"""
import os
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "модель.xlsx")
SHEET = "Себестоимость по этапам"
U = "'Юнит-экономика'"
D = "Допущения"

# Этап, ручных минут без нас (из 5 ч), доля ИИ на этапе, доля токенов ИИ, куда относим прочие расходы
STAGES = [
    ("1. Поиск и отбор закупки", 45, 0.90, 0.10, "данные"),
    ("2. Чтение техзадания и сверка с ассортиментом", 90, 0.85, 0.50, None),
    ("3. Расчёт цены", 30, 0.80, 0.05, None),
    ("4. Заявка и документы (характеристики, декларации, нацрежим)", 90, 0.85, 0.30, None),
    ("5. Подача на площадке и подпись клиента", 15, 0.70, 0.00, "эп"),
    ("6. Итоги, гарантия, подписание контракта, сроки", 30, 0.90, 0.05, "площадка"),
]

YELLOW = PatternFill("solid", fgColor="FFF2CC")
HEAD = PatternFill("solid", fgColor="2F4F4F")


def main():
    wb = load_workbook(PATH)
    if SHEET in wb.sheetnames:
        del wb[SHEET]
    ws = wb.create_sheet(SHEET, wb.sheetnames.index("Юнит-экономика") + 1)

    ws["A1"] = "СЕБЕСТОИМОСТЬ ЗАЯВКИ ПО ЭТАПАМ ТЕНДЕРА (выбранный сценарий). Жёлтое — допущения о разбивке, оценка."
    ws["A1"].font = Font(bold=True)
    ws["A2"] = ("Итог совпадает с «Юнит-экономика»!G13. Ручное время и доля ИИ по этапам подобраны так, чтобы в сумме "
                "давать допущения модели (5 ч и 85%); строка «Сверка с моделью» показывает расхождение, если поменять жёлтые ячейки.")
    ws["A2"].alignment = Alignment(wrap_text=True)
    ws.merge_cells("A2:K2")
    ws.row_dimensions[2].height = 45

    head = ["Этап", "Ручное время без нас, мин", "Доля работы ИИ на этапе", "Минут человека",
            "Труд проверяющего, ₽", "Доля токенов ИИ", "ИИ, ₽", "Данные / подпись / площадка, ₽",
            "Итого на этапе, ₽", "Доля в себестоимости", "Что входит в «прочее»"]
    ws.append([])
    ws.append(head)
    hr = ws.max_row
    for c in ws[hr]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = HEAD
        c.alignment = Alignment(wrap_text=True, vertical="top")

    first = hr + 1
    for name, mins, ai, tok, other in STAGES:
        r = ws.max_row + 1
        if other == "данные":
            oth, note = f"={U}!$G$11", "Доля подписки на данные о закупках (Тендерплан/Контур)"
        elif other == "эп":
            oth, note = f"={U}!$G$10", "Доля разовых расходов на электронную подпись и доверенность"
        elif other == "площадка":
            oth, note = f"={U}!$G$9", "Плата площадке за выигранный контракт × доля побед (в модели — «на нас»)"
        else:
            oth, note = 0, ""
        ws.append([
            name, mins, ai,
            f"=B{r}*(1-C{r})*(1+{D}!$G$32)",
            f"=D{r}/60*{U}!$G$6",
            tok,
            f"=F{r}*{U}!$G$8",
            oth,
            f"=E{r}+G{r}+H{r}",
            None,
            note,
        ])
        for col in "BCF":
            ws[f"{col}{r}"].fill = YELLOW
    last = ws.max_row
    for r in range(first, last + 1):
        ws[f"J{r}"] = f"=I{r}/$I${last + 1}"

    t = last + 1
    ws.append(["ИТОГО", f"=SUM(B{first}:B{last})", f"=1-SUMPRODUCT(B{first}:B{last},1-C{first}:C{last})/B{t}",
               f"=SUM(D{first}:D{last})", f"=SUM(E{first}:E{last})", f"=SUM(F{first}:F{last})",
               f"=SUM(G{first}:G{last})", f"=SUM(H{first}:H{last})", f"=SUM(I{first}:I{last})", f"=SUM(J{first}:J{last})", ""])
    for c in ws[t]:
        c.font = Font(bold=True)
    ws.append(["Сверка с моделью (должно быть 0)", f"=B{t}-{D}!$G$30*60", f"=C{t}-{D}!$G$31", f"=D{t}-{U}!$G$5",
               f"=E{t}-{U}!$G$7", f"=F{t}-1", f"=G{t}-{U}!$G$8", "", f"=I{t}-{U}!$G$13", "", ""])

    ws.append([])
    notes = [
        "Как читать:",
        "• Минут человека = ручное время × (1 − доля ИИ) × (1 + брак и переделки, Допущения!G32).",
        "• Труд = минуты / 60 × стоимость часа проверяющего («Юнит-экономика»!G6: оклад × (1 + налоги) / (часы × загрузка)).",
        "• ИИ = доля токенов этапа × стоимость ИИ на заявку («Юнит-экономика»!G8).",
        "• Плата площадке относится к этапу 6 и платится только при победе. По 44-ФЗ её обычно платит победитель, то есть клиент. "
        "Если так и оставить, себестоимость заявки для нас меньше на эту сумму. Не юридическая консультация, проверить по площадкам.",
        "• Без постоянных расходов (команда, инфраструктура, маркетинг) — они на листе «Модель» и делятся на объём заявок.",
    ]
    for n in notes:
        ws.append([n])
        ws.merge_cells(start_row=ws.max_row, start_column=1, end_row=ws.max_row, end_column=11)
        ws.cell(ws.max_row, 1).alignment = Alignment(wrap_text=True)
        ws.row_dimensions[ws.max_row].height = 30

    widths = [48, 14, 13, 12, 14, 12, 10, 16, 14, 12, 50]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for r in range(first, t + 2):
        for col, fmt in zip("BCDEFGHIJ", ["0", "0%", "0.0", "#,##0", "0%", "#,##0", "#,##0", "#,##0", "0%"]):
            ws[f"{col}{r}"].number_format = fmt
    ws.freeze_panes = f"B{hr + 1}"
    wb.save(PATH)
    print("added sheet", SHEET, "rows", first, "-", t)


if __name__ == "__main__":
    main()
