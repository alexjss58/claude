"""Разбор «Описания объекта закупки» из текста документа (правила + регулярные выражения).

Понимает два вида оформления:
1) таблица «№ | Наименование товара | КТРУ | Наименование характеристики | Значение | Единица | Количество»
   (так выгружают из ЕИС и так делает большинство заказчиков);
2) свободный текст:
      1. Ноутбук — 14 шт. (КТРУ 26.20.11.110-00000139)
      Диагональ экрана: не менее 16 дюймов
      Оперативная память не менее 16 ГБ
"""
from __future__ import annotations

import re

from .conditions import detect_equiv, parse_value
from .models import Position, Purchase, Requirement
from .readers import Doc

KTRU_RE = re.compile(r"\b(\d{2}\.\d{2}\.\d{2}\.\d{3}-\d{8})\b")
OKPD_RE = re.compile(r"окпд\s*2?\)?\s*[:\-–]?\s*(\d{2}\.\d{2}(?:\.\d{1,2}(?:\.\d{3})?)?)", re.I)
OKPD_BARE = re.compile(r"(?<![\d.])(\d{2}\.\d{2}\.\d{2}\.\d{3})(?![\d-])")
NUM44_RE = re.compile(r"(?<!\d)(0\d{18})(?!\d)")
NUM223_RE = re.compile(r"(?<!\d)(3\d{10})(?!\d)")
QTY_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(шт|штук|ед|единиц|компл|комплект|упак)\b\.?", re.I)

PRODUCT_WORDS = (r"ноутбук|компьютер|монитор|\bмфу\b|многофункциональн|принтер|коммутатор|маршрутизатор|телефон|проектор|"
                 r"экран|гарнитур|наушник|бесперебойн|\bибп\b|сервер|моноблок|системный блок|сканер|клавиатур|мыш|камер|"
                 r"планшет|накопител|картридж|кабел|панел|колонк|микрофон|радиостанц|роутер|точка доступа|видеорегистратор|"
                 r"оборудовани|устройств|товар|аппарат")
SECTION_WORDS = (r"требовани|срок|место|гаранти|порядок|условия|оплат|приемк|приёмк|упаковк|маркировк|общие|"
                 r"обоснован|нормативн|документ|перечень|ответственност|адрес")

COLS = [
    ("cunit", [r"единиц\w* измерения характерист", r"ед\.?\s*изм\w*\.?\s*характ"]),
    ("instr", [r"инструкц"]),
    ("char", [r"наименование характерист", r"^характеристик", r"параметр", r"показател", r"наименование показател"]),
    ("value", [r"значени", r"требовани", r"величин"]),
    ("code", [r"ктру", r"окпд", r"^код"]),
    ("qty", [r"кол-?во", r"количеств"]),
    ("qunit", [r"ед\.?\s*изм", r"единиц\w* измерения"]),
    ("name", [r"наименование (товара|позиции|объекта|продукции)", r"^наименование$", r"^товар", r"^предмет", r"^наименование"]),
    ("num", [r"^№", r"п/п", r"^n$", r"^#$"]),
]


def _col_type(cell: str) -> str | None:
    c = (cell or "").strip().lower().replace("ё", "е")
    if not c:
        return None
    for t, pats in COLS:
        if any(re.search(p, c) for p in pats):
            return t
    return None


def _header(rows: list[list[str]]) -> tuple[int, dict[str, int]] | None:
    for i, row in enumerate(rows[:6]):
        m: dict[str, int] = {}
        for j, cell in enumerate(row):
            t = _col_type(cell)
            if t and t not in m:
                m[t] = j
        if ("char" in m and "value" in m) or ("name" in m and ("qty" in m or "value" in m)):
            return i, m
    return None


def _num(s: str) -> float | None:
    m = re.search(r"\d+(?:[.,]\d+)?", s or "")
    return float(m.group(0).replace(",", ".")) if m else None


def _codes(text: str) -> tuple[str, str]:
    k = KTRU_RE.search(text or "")
    o = OKPD_RE.search(text or "") or OKPD_BARE.search(text or "")
    ktru = k.group(1) if k else ""
    okpd = (o.group(1) if o else "") or (ktru.split("-")[0] if ktru else "")
    return ktru, okpd


class _Builder:
    def __init__(self):
        self.positions: list[Position] = []
        self.cur: Position | None = None

    def start(self, name: str, ktru: str = "", okpd: str = "", qty: float | None = None, unit: str = "шт") -> Position:
        pos = Position(num=len(self.positions) + 1, name=name.strip(" .:;—–-"), ktru=ktru, okpd2=okpd,
                       quantity=qty, unit=unit or "шт")
        self.positions.append(pos)
        self.cur = pos
        return pos

    def add(self, name: str, value: str, unit: str = "", instr: str = "") -> Requirement | None:
        if self.cur is None:
            return None
        name = name.strip(" .:;•·-–—*")
        value = value.strip(" ;")
        if not name or not value:
            return None
        r = parse_value(value, name, unit_hint=unit.strip())
        if unit and not r.unit and r.op in (">=", "<=", "=", "диапазон") and r.vmin is not None or (unit and not r.unit and r.vmax is not None):
            r.unit = unit.strip()
        r.instruction = instr
        self.cur.requirements.append(r)
        return r


def _parse_table(rows: list[list[str]], b: _Builder, context_name: str | None) -> bool:
    h = _header(rows)
    if not h:
        return False
    hi, cols = h
    get = lambda row, key: (row[cols[key]].strip() if key in cols and cols[key] < len(row) and row[cols[key]] else "")  # noqa: E731
    last_key = None
    for row in rows[hi + 1:]:
        if not any(row):
            continue
        name, num, code = get(row, "name"), get(row, "num"), get(row, "code")
        char, value = get(row, "char"), get(row, "value")
        # строка-разделитель «1. Ноутбук» во всю ширину
        if not name and not char and value and len(set(c for c in row if c)) == 1 and re.search(PRODUCT_WORDS, value.lower()):
            b.start(value)
            continue
        key = (num, name) if (num or name) else None
        if key and key != last_key and (name or b.cur is None):
            ktru, okpd = _codes(code or name)
            qty = _num(get(row, "qty")) if "qty" in cols else None
            b.start(name or context_name or f"Позиция {num}", ktru, okpd, qty, get(row, "qunit") or "шт")
            last_key = key
        elif b.cur is not None and "qty" in cols and b.cur.quantity is None and get(row, "qty"):
            b.cur.quantity = _num(get(row, "qty"))
        if b.cur is None and context_name:
            b.start(context_name)
        if char and value:
            b.add(char, value, get(row, "cunit"), get(row, "instr"))
        elif "char" not in cols and value and b.cur is not None and name:
            # таблица «Наименование | Требования» — требования одной строкой
            for part in re.split(r";\s*|\n", value):
                m = re.match(r"(.{3,90}?)\s*[:—–]\s*(.+)", part)
                if m:
                    b.add(m.group(1), m.group(2))
    return True


HEAD_RE = re.compile(r"^(?:позиция\s*)?(?:№\s*)?(\d{1,3})[.)]\s+(.{3,200})$", re.I)
NAME_LINE_RE = re.compile(r"^(?:наименование товара|наименование позиции|товар|позиция(?:\s*№?\s*\d+)?)\s*[:—–-]\s*(.{3,200})$", re.I)
CHAR_COLON_RE = re.compile(r"^[-–•*·]?\s*(?P<name>[A-Za-zА-Яа-яЁё0-9(][^:]{1,140}?)\s*(?::|\s[–—]\s)\s*(?P<val>.+)$")
CHAR_COND_RE = re.compile(r"^[-–•*·]?\s*(?P<name>[A-Za-zА-Яа-яЁё][^:]{2,100}?)\s+(?P<val>(?:не\s+менее|не\s+более|не\s+ниже|не\s+выше|не\s+хуже|≥|≤|>=|<=|от\s+\d|более\s+\d|менее\s+\d|наличие|отсутствие)\b.*)$", re.I)
QTY_LINE_RE = re.compile(r"^(?:количество|кол-во)\w*\s*(?:товара)?\s*[:—–-]?\s*(\d+(?:[.,]\d+)?)\s*([а-яa-z.]*)", re.I)
SKIP_CHAR = re.compile(r"^(срок|место|адрес|условия|порядок|оплата|заказчик|поставщик|ктру|окпд|код|количество|кол-во|итого|всего|цена|стоимость|нмц|примечание)", re.I)


def _parse_paragraph(line: str, b: _Builder) -> None:
    t = line.strip()
    low = t.lower()
    m = NAME_LINE_RE.match(t)
    if m:
        name = m.group(1)
        ktru, okpd = _codes(name)
        q = QTY_RE.search(name)
        name = re.sub(r"\(.*?(ктру|окпд).*?\)", "", name, flags=re.I)
        name = QTY_RE.sub("", name) if q else name
        b.start(re.split(r"\s[—–-]\s|,\s*КТРУ|\(КТРУ", name)[0], ktru, okpd, float(q.group(1).replace(",", ".")) if q else None)
        return
    m = HEAD_RE.match(t)
    if m and len(t) < 220:
        body = m.group(2)
        bl = body.lower()
        if re.search(PRODUCT_WORDS, bl) and not re.search(r"^(" + SECTION_WORDS + r")", bl) and ":" not in body.split("—")[0][:60]:
            ktru, okpd = _codes(body)
            q = QTY_RE.search(body)
            name = re.split(r"\s[—–-]\s|\(|,\s*(?:КТРУ|ОКПД)", body)[0]
            b.start(name, ktru, okpd, float(q.group(1).replace(",", ".")) if q else None, (q.group(2) if q else "шт"))
            return
        if re.search(r"^(" + SECTION_WORDS + r")", bl):
            b.cur = None
            return
    if b.cur is None:
        return
    if KTRU_RE.search(t) and not b.cur.ktru:
        b.cur.ktru, b.cur.okpd2 = _codes(t)
        if re.match(r"^(код\s+)?(ктру|окпд)", low):
            return
    m = QTY_LINE_RE.match(t)
    if m:
        b.cur.quantity = float(m.group(1).replace(",", "."))
        if m.group(2):
            b.cur.unit = m.group(2).strip(".") or "шт"
        return
    if SKIP_CHAR.match(t):
        return
    m = CHAR_COLON_RE.match(t) or CHAR_COND_RE.match(t)
    if m:
        b.add(m.group("name"), m.group("val"))


def parse_doc(doc: Doc) -> Purchase:
    pur = Purchase(parser="текст (правила)")
    b = _Builder()
    full = doc.text()
    n = NUM44_RE.search(full) or NUM223_RE.search(full)
    if n:
        pur.number = n.group(1)
        if len(pur.number) == 11:
            pur.law = "223-ФЗ"
    m = re.search(r"(?:объект закупки|предмет (?:закупки|контракта)|наименование объекта закупки)\s*[:—–-]\s*(.+)", full, re.I)
    if m:
        pur.subject = m.group(1).strip()[:300]
    m = re.search(r"заказчик\s*[:—–-]\s*(.+)", full, re.I)
    if m:
        pur.customer = m.group(1).strip()[:300]
    context_name = None
    for kind, blk in doc.blocks:
        if kind == "p":
            before = b.cur
            _parse_paragraph(blk, b)
            if b.cur is not None and b.cur is not before:
                context_name = b.cur.name
        else:
            cur_before = b.cur
            if cur_before is not None and not cur_before.requirements and _header(blk) and "name" not in (_header(blk) or (0, {}))[1]:
                # таблица характеристик сразу под заголовком позиции
                b.positions.pop()
                b.cur = None
                context_name = cur_before.name
                ok = _parse_table(blk, b, context_name)
                if b.positions and b.positions[-1].name == context_name:
                    p = b.positions[-1]
                    p.ktru, p.okpd2 = p.ktru or cur_before.ktru, p.okpd2 or cur_before.okpd2
                    p.quantity = p.quantity if p.quantity is not None else cur_before.quantity
                if not ok:
                    b.positions.append(cur_before)
                    b.cur = cur_before
            else:
                _parse_table(blk, b, None)
    pur.positions = [p for p in b.positions if p.name]
    for i, p in enumerate(pur.positions, 1):
        p.num = i
    if re.search(r"эквивалент\w*\s+не\s+допуска", full, re.I):
        for p in pur.positions:
            for r in p.requirements:
                r.equiv = False
    eq = detect_equiv(full)
    if eq is False:
        for p in pur.positions:
            p.brand_no_equiv = True
    return pur
