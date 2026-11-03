"""Разбор условий («не менее 16 ГБ», «от 8 до 16», «IPS или VA») и проверка значения товара."""
from __future__ import annotations

import re

from . import units
from .models import Requirement, fmt

NUM = r"(\d{1,3}(?:[  ]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?)"
UNIT = r"(\s*[^\d≤≥<>=;,()]{0,18}?)"

EQUIV_YES = re.compile(r"или\s+эквивалент|или\s+аналог|эквивалент\s+допуска|допускается\s+эквивалент|или\s+равнозначн", re.I)
EQUIV_NO = re.compile(r"эквивалент\s+не\s+допуска|без\s+эквивалент|не\s+допускается\s+(?:поставка\s+)?эквивалент|замена\s+[^.]{0,40}не\s+допускается", re.I)

TRUE_WORDS = {"да", "есть", "наличие", "имеется", "присутствует", "поддерживается", "yes", "+", "требуется", "должен быть", "должна быть", "должно быть", "предусмотрен", "предусмотрена", "в наличии"}
FALSE_WORDS = {"нет", "отсутствует", "no", "-", "—", "не поддерживается", "не требуется", "без", "не предусмотрен", "не предусмотрена", "отсутствие"}

RES_RE = re.compile(r"(\d{3,4})\s*[xх×*]\s*(\d{3,4})", re.I)


def _num(s: str) -> float:
    return float(s.replace(" ", "").replace(" ", "").replace(",", "."))


def _norm_space(t: str) -> str:
    return re.sub(r"\s+", " ", (t or "").replace(" ", " ")).strip()


def _unit_ok(u: str) -> str:
    u = (u or "").strip(" .,;:()")
    if not u:
        return ""
    # отрезаем хвост после единицы: «ГБ DDR4» -> «ГБ»
    first = units.unit_after(u)
    return first or ""


def _ua(t: str, m: re.Match, gi: int) -> str:
    """Единица сразу после числовой группы gi совпадения m."""
    if m.group(gi) is None:
        return ""
    return units.unit_after(t[m.end(gi):]) or ""


def detect_equiv(text: str) -> bool | None:
    if EQUIV_NO.search(text or ""):
        return False
    if EQUIV_YES.search(text or ""):
        return True
    return None


def parse_value(text: str, name: str = "", unit_hint: str = "") -> Requirement:
    """Текст требования -> Requirement. name нужен для эвристик (перечень «все»/«одно из»)."""
    raw = _norm_space(text)
    r = Requirement(name=_norm_space(name), raw=raw, value=raw)
    if not raw:
        return r
    eq = detect_equiv(raw)
    if eq is not None:
        r.equiv = eq
    clean = re.sub(r"\(?\s*(?:или\s+эквивалент\w*|или\s+аналог\w*|эквивалент\s+допускается)\s*\)?", "", raw, flags=re.I).strip(" ,;")
    t = clean.lower().replace("ё", "е")
    hint = unit_hint or ""

    def setnum(op, vmin=None, vmax=None, unit="", smin=False, smax=False):
        r.op, r.vmin, r.vmax, r.min_strict, r.max_strict = op, vmin, vmax, smin, smax
        r.unit = unit or hint
        if op == "диапазон":
            r.value = f"{fmt(vmin)}–{fmt(vmax)}"
        else:
            r.value = fmt(vmin if vmin is not None else vmax)
        return r

    # 1) разрешение 1920x1080
    m = RES_RE.search(t)
    if m:
        r.values = [f"{m.group(1)}x{m.group(2)}"]
        r.unit = "пиксель"
        if re.search(r"не\s+менее|не\s+ниже|не\s+хуже|≥|>=|от\b|минимум|и\s+более|и\s+выше", t):
            r.op = ">="
        elif re.search(r"не\s+более|≤|<=", t):
            r.op = "<="
        else:
            r.op = "="
        r.value = r.values[0]
        return r

    # 2) диапазоны
    pats = [
        rf"от\s*{NUM}{UNIT}\s*до\s*{NUM}",
        rf"(?:≥|>=|не\s+менее|не\s+меньше|не\s+ниже)\s*{NUM}{UNIT}\s*(?:и|,|;)?\s*(?:≤|<=|не\s+более|не\s+больше|не\s+выше)\s*{NUM}",
        rf"в\s+диапазоне\s+(?:от\s*)?{NUM}{UNIT}\s*(?:до|[-–—…]|\.\.\.)\s*{NUM}",
    ]
    for p in pats:
        m = re.search(p, t, re.I)
        if m:
            u = _ua(t, m, 3) or _ua(t, m, 1)
            return setnum("диапазон", _num(m.group(1)), _num(m.group(3)), u)
    m = re.fullmatch(rf"{NUM}\s*[-–—]\s*{NUM}(.*)", t)
    if m and _ua(t, m, 2):
        return setnum("диапазон", _num(m.group(1)), _num(m.group(2)), _ua(t, m, 2))

    # 3) нижняя граница
    m = re.search(rf"(не\s+менее|не\s+меньше|не\s+ниже|не\s+хуже|не\s+уже|минимум|минимально|min\.?|≥|>=|⩾)\s*:?\s*{NUM}", t)
    if m:
        return setnum(">=", _num(m.group(2)), None, _ua(t, m, 2))
    m = re.search(rf"{NUM}{UNIT}\s*(и\s+более|и\s+выше|и\s+больше|или\s+более|или\s+выше|\+(?!\w))", t)
    if m:
        return setnum(">=", _num(m.group(1)), None, _ua(t, m, 1))
    m = re.search(rf"(?<!не\s)(?<!не)\b(более|больше|свыше|выше)\s*{NUM}", t) or re.search(rf"(?<![<>])>\s*{NUM}", t)
    if m:
        gi = 2 if m.re.groups >= 2 else 1
        return setnum(">=", _num(m.group(gi)), None, _ua(t, m, gi), smin=True)

    # 4) верхняя граница
    m = re.search(rf"(не\s+более|не\s+больше|не\s+выше|не\s+превыша\w*|максимум|максимально|max\.?|≤|<=|⩽)\s*:?\s*{NUM}", t)
    if m:
        return setnum("<=", None, _num(m.group(2)), _ua(t, m, 2))
    m = re.search(rf"{NUM}{UNIT}\s*(и\s+менее|и\s+ниже|и\s+меньше|или\s+менее)", t)
    if m:
        return setnum("<=", None, _num(m.group(1)), _ua(t, m, 1))
    m = re.search(rf"(?<!не\s)(?<!не)\b(менее|меньше|ниже)\s*{NUM}", t) or re.search(rf"(?<![<>])<\s*{NUM}", t)
    if m:
        gi = 2 if m.re.groups >= 2 else 1
        return setnum("<=", None, _num(m.group(gi)), _ua(t, m, gi), smax=True)
    m = re.fullmatch(rf"до\s*{NUM}(.*)", t)
    if m:
        return setnum("<=", None, _num(m.group(1)), _ua(t, m, 1))

    # 5) одно число (с единицей или без) -> равно
    m = re.fullmatch(rf"=?\s*{NUM}(.*)", t)
    if m and (not m.group(2).strip() or _ua(t, m, 1)):
        r2 = setnum("=", _num(m.group(1)), None, _ua(t, m, 1))
        r2.vmax = r2.vmin
        return r2

    # 6) да / нет
    tt = t.strip(" .;:")
    if tt in TRUE_WORDS or re.match(r"^(наличие|да|есть|имеется)\b", tt):
        r.op, r.values, r.value = "=", ["да"], "да"
        return r
    if tt in FALSE_WORDS or re.match(r"^(нет|отсутств)", tt):
        r.op, r.values, r.value = "=", ["нет"], "нет"
        return r

    # 7) перечень значений
    parts = split_list(clean)
    if len(parts) > 1:
        r.values = parts
        any_of = bool(re.search(r"\s(или|либо)\s|/", clean.lower()))
        name_l = (name or "").lower()
        if not any_of and re.search(r"наличие|интерфейс|порт|разъем|разъём|функци|комплект|поддерж|режим", name_l):
            r.all_values, r.op = True, "="
        else:
            r.op = "из_списка"
        r.value = (" + " if r.all_values else "; ").join(parts)
        return r

    # 8) просто текст
    r.op = "текст"
    r.values = [clean]
    r.value = clean
    return r


def split_list(raw: str) -> list[str]:
    s = raw.strip().rstrip(".")
    if re.search(r"\d+[.,]\d", s) and not re.search(r";", s):
        # «15,6» — не разделитель
        pieces = re.split(r"\s*;\s*|\s+или\s+|\s+либо\s+", s)
    else:
        pieces = re.split(r"\s*[;,]\s*|\s+или\s+|\s+либо\s+|\s*/\s*(?=[A-Za-zА-Яа-я])", s)
    pieces = [p.strip(" .") for p in pieces if p and p.strip(" .")]
    return pieces


# ---------------------------------------------------------------- сравнение

def _cyr_lat(token: str) -> str:
    """В коротких кодах (А4, Wi-Fi) русские буквы-двойники -> латиница."""
    table = str.maketrans("авекмнорстух", "abekmhopctyx")
    return token.translate(table)


VALUE_SYNONYMS = [
    {"ssd", "твердотельн", "nvme", "solid state"},
    {"hdd", "жестк", "жёстк"},
    {"wi-fi", "wifi", "802.11", "wlan", "wi fi"},
    {"bluetooth", "bt "},
    {"type-c", "usb-c", "usb c", "type c", "typec"},
    {"rj-45", "rj45", "8p8c", "ethernet", "gigabit lan", "lan"},
    {"displayport", "display port", " dp"},
    {"vga", "d-sub", "dsub"},
    {"лазерн", "электрографическ", "laser", "электрофотографическ"},
    {"светодиодн", "led"},
    {"струйн", "inkjet"},
    {"черно-бел", "монохром", "ч/б", "чб", "mono", "черно бел"},
    {"цветн", "colou", "color"},
    {"line-interactive", "линейно-интерактив", "интерактивн"},
    {"online", "двойным преобразован", "двойного преобразован", "on-line", "онлайн", "двойное преобразование"},
    {"резервн", "off-line", "offline", "standby", "back"},
    {"чистая синусоида", "синусоида", "sine"},
    {"модифицированная синусоида", "аппроксимированная синусоида", "ступенчат", "modified sine"},
    {"напольн", "tower"},
    {"стоечн", "rack", "в стойку", "19"},
    {"планшетн", "flatbed"},
    {"протяжн", "автоподатчик", "adf"},
    {"ips", "ips-type", "ahva"},
    {"va", "mva"},
    {"tn"},
    {"oled"},
    {"dlp"},
    {"lcd", "3lcd", "жк"},
    {"лазерный источник", "laser phosphor", "лазер"},
    {"usb"},
    {"hdmi"},
    {"l2", "второго уровня", "уровня 2"},
    {"l3", "третьего уровня", "уровня 3"},
    {"управляем", "managed"},
    {"poe", "802.3af", "802.3at", "poe+"},
    {"sfp+", "10gbase", "10g"},
    {"ddr4"}, {"ddr5"}, {"ddr3"},
    {"windows"},
    {"linux", "astra", "альт", "ред ос", "red os", "основа", "эльбрус"},
    {"usb-a", "type-a", "usb a"},
    {"моно", "mono", "одно ух"},
    {"стерео", "stereo", "duo", "два уха", "двух ух"},
    {"матов", "антиблик", "matte"},
    {"глянц", "glossy"},
    {"a4", "а4"}, {"a3", "а3"},
]


def norm_text(s: str) -> str:
    s = (s or "").lower().replace("ё", "е").replace(" ", " ")
    s = re.sub(r"\s+", " ", s)
    s = " ".join(_cyr_lat(w) if re.search(r"\d", w) and len(w) <= 5 else w for w in s.split(" "))
    return " " + s + " "


def text_has(product_text: str, value: str) -> bool:
    """Есть ли значение value (с синонимами) в тексте товара."""
    p = norm_text(product_text)
    v = norm_text(value).strip()
    if not v:
        return False
    if v in p:
        return True
    for group in VALUE_SYNONYMS:
        if any(g.strip() and g.strip() in v for g in group):
            if any(g.strip() and g.strip() in p for g in group):
                # для групп «моно/стерео», «ч/б/цвет» проверяем, что значение именно из этой группы
                return True
    # все значимые слова значения есть в тексте товара
    words = [w for w in re.findall(r"[a-zа-я0-9+\-.]{3,}", v)]
    return bool(words) and all(w in p for w in words)


def truthy(s: str) -> bool | None:
    if s is None:
        return None
    t = str(s).strip().lower().replace("ё", "е")
    if t == "" or t == "nan":
        return None
    if t in FALSE_WORDS or t.startswith("нет") or t.startswith("отсутств") or t == "0":
        return False
    return True


def numbers_in(s: str) -> list[float]:
    return units.all_numbers(str(s))


def _tol(dim: str | None) -> float:
    return 0.025 if dim == "data" else 0.005


def compare(req: Requirement, have_raw, have_unit: str | None = None) -> tuple[str, str]:
    """Проверить значение товара. -> (ok|fail|unknown, текст значения товара)."""
    if have_raw is None:
        return "unknown", ""
    have = str(have_raw).strip()
    if have == "" or have.lower() == "nan":
        return "unknown", ""
    shown = have + (f" {have_unit}" if have_unit and not re.search(r"[a-zа-я]", have.lower()) else "")

    # разрешение
    if req.unit == "пиксель" and req.values and RES_RE.search(req.values[0]):
        need = RES_RE.search(req.values[0])
        got = RES_RE.search(have)
        if not got:
            return "unknown", shown
        nw, nh = int(need.group(1)), int(need.group(2))
        gw, gh = int(got.group(1)), int(got.group(2))
        if req.op == ">=":
            ok = max(gw, gh) >= max(nw, nh) and min(gw, gh) >= min(nw, nh)
        elif req.op == "<=":
            ok = max(gw, gh) <= max(nw, nh) and min(gw, gh) <= min(nw, nh)
        else:
            ok = {gw, gh} == {nw, nh}
        return ("ok" if ok else "fail"), shown

    if req.op in (">=", "<=", "диапазон") or (req.op == "=" and req.vmin is not None and not req.values):
        nums = numbers_in(have)
        if not nums:
            tv = truthy(have)
            if tv is False and req.op == ">=" and (req.vmin or 0) > 0:
                return "fail", shown
            return "unknown", shown
        hu = have_unit or units.find_unit(have) or ""
        ru = req.unit or ""
        conv = []
        for n in nums:
            if ru and hu:
                c = units.convert(n, hu, ru)
                if c is None:
                    continue
                conv.append(c)
            else:
                conv.append(n)
        if not conv:
            return "unknown", shown
        lk = units.lookup(ru) or units.lookup(hu)
        tol = _tol(lk[0] if lk else None)
        if req.op == ">=":
            v = max(conv)
            ok = v > req.vmin if req.min_strict else v >= req.vmin * (1 - tol)
        elif req.op == "<=":
            v = min(conv)
            ok = v < req.vmax if req.max_strict else v <= req.vmax * (1 + tol)
        elif req.op == "диапазон":
            ok = any(req.vmin * (1 - tol) <= v <= req.vmax * (1 + tol) for v in conv)
        else:
            ok = any(abs(v - req.vmin) <= abs(req.vmin) * tol + 1e-9 for v in conv)
        return ("ok" if ok else "fail"), shown

    # да / нет
    if req.values and req.values[0] in ("да", "нет") and len(req.values) == 1:
        tv = truthy(have)
        if tv is None:
            return "unknown", shown
        want = req.values[0] == "да"
        return ("ok" if tv == want else "fail"), shown

    # текстовые значения
    vals = req.values or ([req.value] if req.value else [])
    if not vals:
        return "unknown", shown
    hits = [text_has(have, v) for v in vals]
    if req.all_values:
        ok = all(hits)
    else:
        ok = any(hits)
    if ok:
        return "ok", shown
    if req.op == "текст":
        # свободный текст сравнить надёжно нельзя
        return "unknown", shown
    return "fail", shown
