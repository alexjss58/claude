"""Собирает результаты блока A в результаты/поставщики_75.xlsx.

Вход: _работа/A_выход_part1..5.json (первый проход) и A_выход_part6..8.json (второй проход
по тем, кого не успели или не нашли). Второй проход перекрывает первый, если в нём больше данных.
Ручные правки (если есть) — _работа/A_правки.json: {"<лист>|<№>": {поле: значение, ...}}.
"""
import json, os, re
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))          # для_облака/
SRC = os.path.join(ROOT, "данные", "Suppliers_top3_niches_3nov.xlsx")
OUT = os.path.join(ROOT, "результаты", "поставщики_75.xlsx")
SHEETS = ['Связь и аудио-видео 26.3-26.4', 'Приборы 26.51', 'Лабреактивы 20.59.52']
FIELDS = ["ИНН", "ОГРН", "регион", "сайт", "почта", "телефон", "руководитель", "профиль"]


def filled(c):
    return sum(1 for f in FIELDS if c.get(f))


def load_results():
    res = {}
    for i in range(1, 9):
        p = os.path.join(HERE, f"A_выход_part{i}.json")
        if not os.path.exists(p):
            continue
        for c in json.load(open(p, encoding="utf-8")):
            k = (c["лист"], int(c["№"]))
            if k not in res or filled(c) >= filled(res[k]):
                res[k] = c
    p = os.path.join(HERE, "A_правки.json")
    if os.path.exists(p):
        for key, upd in json.load(open(p, encoding="utf-8")).items():
            sheet, n = key.split("|")
            res.setdefault((sheet, int(n)), {}).update(upd)
    return res


def main_source(c):
    src = c.get("источники") or {}
    rel = c.get("надёжность") or {}
    for f in ["почта", "телефон", "сайт", "ИНН", "профиль", "руководитель"]:
        if src.get(f):
            return src[f], rel.get(f)
    return None, None


def all_sources(c):
    src = c.get("источники") or {}
    rel = c.get("надёжность") or {}
    parts = []
    for f, u in src.items():
        if u:
            parts.append(f"{f}: {u} ({rel.get(f, '—')})")
    return "\n".join(parts) or None


def letter_type(drop):
    if drop is None or (isinstance(drop, float) and pd.isna(drop)):
        return "неясно"
    if drop <= 7:
        return "а — свои закупки, важны скорость и надёжность"
    if drop > 25:
        return "б — ценовой боец, важен расчёт цены"
    return "средний (7–25%)"


def is_email(s):
    return bool(s) and bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", str(s)))


def build():
    res = load_results()
    wb = Workbook()
    wb.remove(wb.active)
    head_font = Font(bold=True, color="FFFFFF")
    head_fill = PatternFill("solid", fgColor="2F4F4F")
    best_rows = []
    stats = {}
    for sh in SHEETS:
        df = pd.read_excel(SRC, sheet_name=sh)
        ws = wb.create_sheet(sh[:31])
        cols = ["№", "Поставщик", "Участий за квартал", "Побед", "% побед", "Среднее снижение, %",
                "Контрактов на сумму, ₽", "Последнее участие", "Карточка в Тендерплане",
                "ИНН", "ОГРН/ОГРНИП", "Регион", "Сайт", "Почта", "Телефон", "Руководитель",
                "Профиль (чем торгует)", "Малый бизнес без тендерного отдела? (да/нет/неясно)",
                "Почему так", "Источник (URL)", "Надёжность", "Все источники по полям", "Примечание",
                "Тип письма (блок B)", "Статус письма"]
        ws.append(cols)
        n_inn = n_mail = n_tel = 0
        for _, r in df.iterrows():
            k = (sh, int(r["№"]))
            c = res.get(k, {})
            src, rel = main_source(c)
            drop = None if pd.isna(r["Среднее снижение, %"]) else round(float(r["Среднее снижение, %"]), 1)
            row = [int(r["№"]), str(r["Поставщик"]).strip(), int(r["Участий за квартал"]), int(r["Побед"]),
                   None if pd.isna(r["% побед"]) else round(float(r["% побед"]), 1), drop,
                   None if pd.isna(r["Контрактов на сумму, ₽"]) else int(r["Контрактов на сумму, ₽"]),
                   None if pd.isna(r["Последнее участие"]) else str(r["Последнее участие"]),
                   None if pd.isna(r["Карточка в Тендерплане"]) else str(r["Карточка в Тендерплане"]),
                   c.get("ИНН"), c.get("ОГРН"), c.get("регион"), c.get("сайт"), c.get("почта"),
                   c.get("телефон"), c.get("руководитель"), c.get("профиль"),
                   c.get("малый_без_тендерного_отдела") or "неясно", c.get("обоснование_малый"),
                   src, rel, all_sources(c), c.get("примечание"), letter_type(drop), None]
            ws.append(row)
            n_inn += bool(c.get("ИНН")); n_mail += is_email(c.get("почта")); n_tel += bool(c.get("телефон"))
            if is_email(c.get("почта")):
                best_rows.append((sh, row, c))
        stats[sh] = (len(df), n_inn, n_mail, n_tel)
        fmt(ws, head_font, head_fill)

    # Лучшие 30: 10 на нишу. Нужна деловая почта и профиль по нише.
    # Порядок: сначала «малый без тендерного отдела» = да, потом «неясно», потом «нет»;
    # внутри — по числу побед за квартал (больше побед — больше заявок, тем ценнее «+10 заявок без найма»).
    ws = wb.create_sheet("Лучшие 30", 0)
    cols = ["Ниша", "№ в нише", "Компания", "Руководитель", "Почта", "Телефон", "Сайт", "ИНН", "Регион",
            "Профиль", "Участий за квартал", "Побед", "Среднее снижение, %", "Контрактов на сумму, ₽",
            "Тип письма", "Малый без тендерного отдела?", "Почему в списке", "Надёжность почты",
            "Источник почты", "Статус письма"]
    ws.append(cols)
    order = {"да": 0, "неясно": 1, "нет": 2}
    picked_total = 0
    for sh in SHEETS:
        cand = [(row, c) for s, row, c in best_rows if s == sh and c.get("профиль")]
        cand.sort(key=lambda rc: (order.get(rc[1].get("малый_без_тендерного_отдела") or "неясно", 1), -rc[0][3]))
        for row, c in cand[:10]:
            why = (f"{row[3]} побед из {row[2]} участий за квартал; "
                   f"есть деловая почта; малый без тендерного отдела: {c.get('малый_без_тендерного_отдела') or 'неясно'}")
            ws.append([sh, row[0], row[1], c.get("руководитель"), c.get("почта"), c.get("телефон"), c.get("сайт"),
                       c.get("ИНН"), c.get("регион"), c.get("профиль"), row[2], row[3], row[5], row[6],
                       row[23], c.get("малый_без_тендерного_отдела") or "неясно", why,
                       (c.get("надёжность") or {}).get("почта"), (c.get("источники") or {}).get("почта"), None])
            picked_total += 1
        if len(cand) < 10:
            ws.append([sh, None, f"⚠ Нашлось только {len(cand)} компаний с почтой и профилем — добрать вручную"])
    fmt(ws, head_font, head_fill)

    # Лист-инструкция
    wi = wb.create_sheet("Как пользоваться", 1)
    lines = [
        "Поставщики_75: контакты 75 лидеров трёх ниш (блок A). Собрано 3–4 ноября 2026 по открытым источникам.",
        "Лист «Лучшие 30» — с кого начать: у всех есть деловая почта и понятный профиль. Тексты писем — в письма_30.xlsx (блок B).",
        "Надёжность: «подтверждено на сайте компании» — видели на сайте; «из справочника» — rusprofile/checko/list-org и т. п.; «предположение» — проверить перед письмом.",
        "Пустая ячейка = не нашли. Ничего не додумывали. Для ИП — только деловые контакты бизнеса.",
        "Тип письма: «а» — среднее снижение ≤7% (свои закупки, важны скорость и надёжность), «б» — снижение >25% (ценовые бойцы, важен расчёт цены).",
        "Перед отправкой: проверить почту на сайте компании (2 минуты), если надёжность не «подтверждено на сайте компании».",
        "",
        "Итог по нишам (компаний / с ИНН / с почтой / с телефоном):",
    ] + [f"  {sh}: {a} / {b} / {c} / {d}" for sh, (a, b, c, d) in stats.items()] + [f"  В «Лучших 30» отобрано: {picked_total}"]
    for l in lines:
        wi.append([l])
    wi.column_dimensions["A"].width = 140
    wb.save(OUT)
    print("saved", OUT, stats, "best:", picked_total)


def fmt(ws, head_font, head_fill):
    for cell in ws[1]:
        cell.font = head_font
        cell.fill = head_fill
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "C2"
    for i, col in enumerate(ws.columns, 1):
        width = max(len(str(c.value)) if c.value is not None else 0 for c in col)
        ws.column_dimensions[get_column_letter(i)].width = min(max(10, width * 0.9), 45)
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
            if isinstance(c.value, str) and c.value.startswith("http"):
                c.hyperlink = c.value
                c.font = Font(color="1F4E99", underline="single")


if __name__ == "__main__":
    build()
