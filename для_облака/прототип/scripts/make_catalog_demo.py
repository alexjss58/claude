"""Демо-каталог движка сверки (../движок/каталог_демо.xlsx) -> src/data/catalog_demo.json.

Каталог широкий: первые 10 столбцов служебные (артикул, категория, производитель, модель, примечание,
реестр, ОКПД2, источник, надёжность, дата), остальные ~150 — характеристики. Пустая ячейка = данных нет.
Цен в каталоге нет, поле цены остаётся пустым (не выдумываем).
Запуск: python3 scripts/make_catalog_demo.py <каталог.xlsx> <выход.json>   (нужен openpyxl)
"""
import json
import sys

import openpyxl

src, dst = sys.argv[1], sys.argv[2]
wb = openpyxl.load_workbook(src, data_only=True)
ws = wb['каталог'] if 'каталог' in wb.sheetnames else wb.worksheets[0]
rows = list(ws.iter_rows(values_only=True))
head = [str(h or '').strip() for h in rows[0]]


def col(prefix):
    for i, h in enumerate(head):
        if h.lower().startswith(prefix.lower()):
            return i
    return None


I = {k: col(k) for k in ['Артикул', 'Категория', 'Производитель', 'Модель', 'Конфигурация', 'Реестр', 'ОКПД2', 'Источник', 'Надёжность', 'Дата проверки']}
service = {v for v in I.values() if v is not None}


def fmt(v):
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


CAT = {'ip-телефон': 'IP-телефон', 'ибп': 'ИБП', 'мфу': 'МФУ'}
items = []
for r in rows[1:]:
    if not r or not r[I['Артикул']]:
        continue
    g = lambda k: (fmt(r[I[k]]) if I[k] is not None and r[I[k]] not in (None, '') else '')
    specs = {head[i]: fmt(v) for i, v in enumerate(r) if i not in service and v not in (None, '')}
    cat_raw = g('Категория')
    cat = CAT.get(cat_raw.lower(), cat_raw[:1].upper() + cat_raw[1:])
    name = f"{g('Производитель')} {g('Модель')}".strip()
    items.append({
        'артикул': g('Артикул'),
        'наименование': name,
        'категория': cat,
        'производитель': g('Производитель'),
        'модель': g('Модель'),
        'характеристики': specs,
        'характеристики_текст': '; '.join(f'{k}: {v}' for k, v in specs.items()),
        'страна': '',
        'цена': None,
        'остаток': None,
        'реестр': g('Реестр'),
        'окпд2': g('ОКПД2'),
        'источник_url': g('Источник'),
        'примечание': g('Конфигурация'),
    })
json.dump(items, open(dst, 'w', encoding='utf-8'), ensure_ascii=False)
print(f'[catalog] {len(items)} моделей, {len({i["категория"] for i in items})} категорий')
