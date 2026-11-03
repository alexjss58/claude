"""Единицы измерения: распознавание и приведение к базовой единице.

Идея простая: у каждой единицы есть «измерение» (объём данных, частота, длина…)
и множитель к базовой единице этого измерения. Сравниваем только числа
одного измерения, приведённые к базе.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# измерение -> базовая единица (для вывода)
BASE = {
    "data": "ГБ",
    "freq": "Гц",
    "len": "мм",
    "power": "Вт",
    "va": "ВА",
    "energy": "Вт·ч",
    "mass": "кг",
    "time": "с",
    "ppm": "стр/мин",
    "dpi": "dpi",
    "rate": "Мбит/с",
    "lum": "кд/м²",
    "lm": "лм",
    "mpx": "Мп",
    "count": "шт",
    "charge": "А·ч",
    "pct": "%",
    "deg": "°",
    "volt": "В",
    "pps": "Мпакетов/с",
    "sheets": "лист",
    "pages": "стр",
    "db": "дБ",
    "gsm": "г/м²",
    "px": "пиксель",
}

# псевдоним (в нижнем регистре, без точек) -> (измерение, множитель к базе)
_ALIASES: dict[str, tuple[str, float]] = {}


def _add(dim: str, factor: float, *names: str) -> None:
    for n in names:
        _ALIASES[n] = (dim, factor)


_add("data", 1 / 1024 / 1024, "кб", "кбайт", "kb", "кбайта", "килобайт")
_add("data", 1 / 1024, "мб", "мбайт", "mb", "мегабайт", "мбайта")
_add("data", 1.0, "гб", "гбайт", "gb", "гигабайт", "гигабайта", "гбайта", "гиб", "gib")
_add("data", 1024.0, "тб", "тбайт", "tb", "терабайт", "терабайта", "тбайта", "tib")
_add("freq", 1e9, "ггц", "ghz", "гигагерц")
_add("freq", 1e6, "мгц", "mhz", "мегагерц")
_add("freq", 1e3, "кгц", "khz", "килогерц")
_add("freq", 1.0, "гц", "hz", "герц")
_add("len", 25.4, "дюйм", "дюйма", "дюймов", "дюймы", '"', "”", "inch", "in", "''")
_add("len", 1.0, "мм", "mm", "миллиметр", "миллиметра", "миллиметров")
_add("len", 10.0, "см", "cm", "сантиметр", "сантиметра", "сантиметров")
_add("len", 1000.0, "м", "m", "метр", "метра", "метров")
_add("power", 1.0, "вт", "w", "ватт", "ватта")
_add("power", 1000.0, "квт", "kw", "киловатт")
_add("va", 1.0, "ва", "va", "в·а", "в*а", "вольт-ампер")
_add("va", 1000.0, "ква", "kva")
_add("energy", 1.0, "вт·ч", "втч", "вт*ч", "wh", "вт ч", "вт/ч")
_add("mass", 1.0, "кг", "kg", "килограмм", "килограмма")
_add("mass", 0.001, "г", "g", "грамм", "грамма")
_add("time", 0.001, "мс", "ms", "миллисекунд", "миллисекунда", "миллисекунды")
_add("time", 1.0, "с", "сек", "s", "секунд", "секунда", "секунды")
_add("time", 60.0, "мин", "min", "минут", "минута", "минуты")
_add("time", 3600.0, "ч", "час", "часов", "часа", "h")
_add("ppm", 1.0, "стр/мин", "стр./мин", "ppm", "страниц в минуту", "стр в минуту", "листов в минуту", "изобр/мин")
_add("dpi", 1.0, "dpi", "точек/дюйм", "точек на дюйм", "т/д", "т/дюйм")
_add("rate", 0.001, "кбит/с", "kbps", "кбит/c")
_add("rate", 1.0, "мбит/с", "mbps", "мбит/c", "мбит", "mbit/s")
_add("rate", 1000.0, "гбит/с", "gbps", "гбит/c", "гбит", "gbit/s", "гб/с")
_add("rate", 1e6, "тбит/с", "tbps")
_add("lum", 1.0, "кд/м2", "кд/м²", "cd/m2", "cd/m²", "нит", "nit", "кд/кв.м", "кд/кв м")
_add("lm", 1.0, "лм", "lm", "люмен", "ansi лм", "ansi lumens", "ansi люмен")
_add("mpx", 1.0, "мп", "мпиксель", "мпикс", "мегапиксель", "мегапикселя", "mp", "мпх")
_add("count", 1.0, "шт", "штук", "штуки", "штука", "ед", "единиц", "единица", "порт", "порта", "портов", "ядер", "ядра", "потоков")
_add("charge", 1.0, "ач", "а·ч", "ah", "а*ч")
_add("charge", 0.001, "мач", "ма·ч", "mah")
_add("pct", 1.0, "%", "процент", "процентов")
_add("deg", 1.0, "°", "град", "градус", "градусов", "градуса")
_add("volt", 1.0, "в", "v", "вольт")
_add("pps", 1.0, "mpps", "мпак/с", "млн пакетов/с", "мпакетов/с")
_add("sheets", 1.0, "лист", "листов", "листа", "листы")
_add("pages", 1.0, "стр", "страниц", "страница", "страницы", "отпечатков", "оттисков")
_add("db", 1.0, "дб", "db", "дб(а)", "dba")
_add("gsm", 1.0, "г/м2", "г/м²", "г/кв.м", "gsm")
_add("px", 1.0, "пиксель", "пикселей", "пикс", "px", "точек", "пиксела")

# Единицы ОКЕИ из ЕИС: национальное обозначение -> наш псевдоним
OKEI_CODE = {
    "2553": "гб", "2554": "тб", "2552": "мб", "2551": "кб",
    "039": "дюйм", "003": "мм", "004": "см", "006": "м",
    "293": "ггц", "292": "мгц", "290": "гц", "291": "кгц",
    "212": "вт", "214": "квт", "245": "вт·ч",
    "166": "кг", "163": "г",
    "355": "мин", "354": "с", "356": "ч",
    "796": "шт", "744": "%",
    "2355": "градус", "222": "в",
    "9642": "стр/мин", "2281": "dpi",
    "2489": "мбит/с", "2490": "гбит/с",
}

_NUM_RE = re.compile(r"[-+]?\d{1,3}(?:[  ]\d{3})+(?:[.,]\d+)?|[-+]?\d+(?:[.,]\d+)?")


def parse_number(s: str) -> float | None:
    """Первое число в строке: «1 000», «15,6», «2.5» -> float."""
    if s is None:
        return None
    m = _NUM_RE.search(str(s))
    if not m:
        return None
    t = m.group(0).replace(" ", "").replace(" ", "").replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def all_numbers(s: str) -> list[float]:
    out = []
    for m in _NUM_RE.finditer(str(s or "")):
        t = m.group(0).replace(" ", "").replace(" ", "").replace(",", ".")
        try:
            out.append(float(t))
        except ValueError:
            pass
    return out


def _clean(u: str) -> str:
    u = (u or "").strip().lower().replace("ё", "е")
    u = u.replace("²", "2") if u not in ("кд/м²", "cd/m²", "г/м²") else u
    u = re.sub(r"\s+", " ", u)
    u = u.rstrip(".")
    return u


def lookup(unit: str) -> tuple[str, float] | None:
    """(измерение, множитель) для обозначения единицы или None."""
    if not unit:
        return None
    u = _clean(unit)
    if u in _ALIASES:
        return _ALIASES[u]
    u2 = u.replace(".", "").replace(" ", "")
    for k, v in _ALIASES.items():
        if k.replace(".", "").replace(" ", "") == u2:
            return v
    return None


# Порядок важен: длинные обозначения раньше коротких (ГГц раньше Гц, Гбит/с раньше Гб)
_UNIT_PATTERNS = sorted(_ALIASES.keys(), key=len, reverse=True)
_UNIT_RE = re.compile(
    r"^\s*(" + "|".join(re.escape(p) for p in _UNIT_PATTERNS) + r")(?![а-яa-z])",
    re.IGNORECASE,
)


def unit_after(text: str) -> str | None:
    """Единица, которая стоит сразу после числа (начало строки text)."""
    t = (text or "").replace("ё", "е")
    m = _UNIT_RE.match(t.lower())
    if m:
        return m.group(1)
    return None


def find_unit(text: str) -> str | None:
    """Первая единица после первого числа в тексте."""
    m = _NUM_RE.search(text or "")
    if not m:
        return None
    return unit_after(text[m.end():])


def unit_from_header(header: str) -> str | None:
    """Единица из заголовка столбца: «Оперативная память, ГБ» -> «ГБ»."""
    if not header:
        return None
    m = re.search(r",\s*([^,()]+)\s*$", header)
    if m and lookup(m.group(1)):
        return m.group(1).strip()
    m = re.search(r"\(([^()]+)\)\s*$", header)
    if m and lookup(m.group(1)):
        return m.group(1).strip()
    return None


@dataclass
class Quantity:
    value: float
    dim: str | None
    factor: float = 1.0

    @property
    def base(self) -> float:
        return self.value * self.factor


def to_quantity(value: float, unit: str | None) -> Quantity:
    lk = lookup(unit) if unit else None
    if lk:
        return Quantity(value, lk[0], lk[1])
    return Quantity(value, None, 1.0)


def same_dim(a: Quantity, b: Quantity) -> bool:
    return a.dim is None or b.dim is None or a.dim == b.dim


def convert(value: float, unit_from: str | None, unit_to: str | None) -> float | None:
    """Перевод числа между единицами одного измерения. None — если нельзя."""
    if not unit_from or not unit_to:
        return value
    a, b = lookup(unit_from), lookup(unit_to)
    if not a or not b:
        return value
    if a[0] != b[0]:
        return None
    return value * a[1] / b[1]


def pretty_unit(unit: str | None) -> str:
    """Короткое человекочитаемое обозначение единицы."""
    if not unit:
        return ""
    lk = lookup(unit)
    if not lk:
        return unit
    dim, f = lk
    table = {
        ("data", 1.0): "ГБ", ("data", 1024.0): "ТБ", ("data", 1 / 1024): "МБ",
        ("freq", 1e9): "ГГц", ("freq", 1e6): "МГц", ("freq", 1.0): "Гц",
        ("len", 25.4): "дюйм", ("len", 1.0): "мм", ("len", 10.0): "см", ("len", 1000.0): "м",
        ("power", 1.0): "Вт", ("va", 1.0): "ВА", ("mass", 1.0): "кг", ("time", 0.001): "мс",
        ("time", 1.0): "с", ("time", 60.0): "мин", ("time", 3600.0): "ч",
        ("ppm", 1.0): "стр/мин", ("dpi", 1.0): "dpi", ("rate", 1.0): "Мбит/с",
        ("rate", 1000.0): "Гбит/с", ("lum", 1.0): "кд/м²", ("lm", 1.0): "лм",
        ("mpx", 1.0): "Мп", ("count", 1.0): "шт", ("pct", 1.0): "%", ("deg", 1.0): "°",
        ("energy", 1.0): "Вт·ч", ("charge", 1.0): "А·ч", ("sheets", 1.0): "лист",
        ("pages", 1.0): "стр",
    }
    return table.get((dim, f), unit)
