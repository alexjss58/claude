"""Разбор условий («не менее 16 ГБ», «от 8 до 16», «IPS или VA») и проверка значения товара."""
from __future__ import annotations

import re

from . import units
from .models import Requirement, fmt

NUM = r"((?<![\d.,])-?\d{1,3}(?:[  ]\d{3})+(?:[.,]\d+)?|(?<![\d.,])-?\d+(?:[.,]\d+)?)"
UNIT = r"(\s*[^\d≤≥<>=;,()]{0,18}?)"

EQUIV_YES = re.compile(r"или\s+эквивалент|или\s+аналог|эквивалент\s+допуска|допускается\s+эквивалент|или\s+равнозначн", re.I)
EQUIV_NO = re.compile(r"эквивалент\s+не\s+допуска|без\s+эквивалент|не\s+допускается\s+(?:поставка\s+)?эквивалент|замена\s+[^.]{0,40}не\s+допускается", re.I)

TRUE_WORDS = {"да", "есть", "наличие", "имеется", "присутствует", "поддерживается", "yes", "+", "требуется", "должен быть", "должна быть", "должно быть", "предусмотрен", "предусмотрена", "в наличии"}
FALSE_WORDS = {"нет", "отсутствует", "no", "-", "—", "не поддерживается", "не требуется", "без", "не предусмотрен", "не предусмотрена", "отсутствие"}

NAMED_RES = [(r"\b(4k|uhd|ultra hd)\b", "3840x2160"), (r"\bwuxga\b", "1920x1200"), (r"\b(wqhd|qhd|2k)\b", "2560x1440"),
             (r"full ?hd|\bfhd\b|1080p", "1920x1080"), (r"\bwxga\b", "1280x800"), (r"\bxga\b", "1024x768"),
             (r"\bhd\b|720p", "1366x768")]
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

    # 1) разрешение 1920x1080 (или названием: Full HD, WUXGA, 4K…)
    if not RES_RE.search(t):
        for pat, wh in NAMED_RES:
            if re.search(pat, t):
                t = t + " " + wh
                break
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

    # 5) одно число (с единицей или без) -> равно; номера версий («2.0») оставляем текстом
    m = None if re.search(r"верси|ревизи|стандарт|поколени", (name or "").lower()) else re.fullmatch(rf"=?\s*{NUM}(.*)", t)
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

    # 8) одно текстовое значение («SSD», «Ноутбук») — это «=»; длинное описание — «текст»
    r.op = "=" if len(clean) <= 60 and not re.search(r"[.!?]\s", clean) else "текст"
    r.values = [clean]
    r.value = clean
    return r


def split_list(raw: str) -> list[str]:
    """Разбить перечень значений. Не режем внутри скобок и десятичные «15,6» / «3.5»."""
    s = raw.strip().rstrip(".")
    out, buf, depth, i = [], "", 0, 0
    seps = re.compile(r";\s*|,\s+(?=\D)|\s+или\s+|\s+либо\s+|\s*/\s*(?=[A-Za-zА-Яа-я])")
    while i < len(s):
        ch = s[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if depth == 0:
            m = seps.match(s, i)
            if m and m.end() > i:
                out.append(buf)
                buf = ""
                i = m.end()
                continue
        buf += ch
        i += 1
    out.append(buf)
    return [p.strip(" .") for p in out if p and p.strip(" .")]


def _cyr_lat(token: str) -> str:
    """В коротких кодах (А4, Wi-Fi) русские буквы-двойники -> латиница."""
    table = str.maketrans("авекмнорстух", "abekmhopctyx")
    return token.translate(table)


# Группы синонимов. Группы внутри одного «семейства» взаимоисключают друг друга
# (если требование «цветная», а у товара «черно-белая» — это явное несоответствие).
FAMILIES = [
    [{"черно-бел", "монохром", "ч/б", "чб", "mono", "черно бел"}, {"цветн", "colou", "color"}],
    [{"лазерн", "электрографическ", "laser", "электрофотографическ"}, {"струйн", "inkjet"}],
    [{"line-interactive", "линейно-интерактив", "интерактивн"}, {"online", "двойным преобразован", "двойного преобразован", "on-line", "онлайн", "двойное преобразование"}, {"резервн", "off-line", "offline", "standby"}],
    [{"чистая синусоида", "sine wave", "синусоида"}, {"модифицированная синусоида", "аппроксимированная синусоида", "ступенчат", "modified sine"}],
    [{"ips", "ips-type", "ahva", "pls", "ads"}, {" va ", "mva", "va-"}, {" tn", "tn+"}, {"oled"}],
    [{"dlp"}, {"3lcd", " lcd"}],
    [{"a4", "а4"}, {"a3", "а3"}],
    [{"ssd", "твердотельн", "nvme", "solid state"}, {"hdd", "жестк", "магнитн"}],
    [{"интегрированн", "встроенн", "integrated"}, {"дискретн", "discrete"}],
    [{"внешн", "external"}, {"встроенн", "внутренн", "internal"}],
    [{"моно", "mono", "одним наушник", "один наушник", "одного наушник", "монаур"}, {"стерео", "stereo", "duo", "двумя наушник", "два наушник", "двух наушник", "бинаур"}],
    [{"напольн", "отдельно стоящ", "tower"}, {"стоечн", "rack", "в стойку"}],
    [{"фиксированн", "fixed"}, {"модульн", "шасси", "modular"}],
    [{"сменн", "hot-swap", "горячей замен", "hot swap"}, {"несменн", "фиксированн"}],
    [{"l2", "второго уровня", "уровня 2"}, {"l3", "третьего уровня", "уровня 3"}],
    [{"неуправляем", "unmanaged"}, {"управляем", "managed"}],
    [{"матов", "антиблик", "matte"}, {"глянц", "glossy"}],
    [{"ddr4"}, {"ddr5"}, {"ddr3"}],
    [{"планшетн", "flatbed"}, {"протяжн", "автоподатчик", "adf"}],
]

# Группы-«интерфейсы»: для закрытых перечней (все порты товара перечислены) отсутствие = несоответствие
VALUE_SYNONYMS = [
    {"wi-fi", "wifi", "802.11", "wlan", "wi fi"},
    {"bluetooth", "bt "},
    {"type-c", "usb-c", "usb c", "type c", "typec", "usb4"},
    {"rj-45", "rj45", "8p8c", "ethernet", "gigabit lan", " lan", "медн", "base-t", "витая пара"},
    {"displayport", "display port", " dp", "minidp"},
    {"vga", "d-sub", "dsub"},
    {"hdmi"},
    {"dvi"},
    {"usb"},
    {"mini-jack", "minijack", "mini jack", "jack", "3,5 мм", "3.5 мм", "аудиовыход", "аудиовход", "аудио", "audio"},
    {"m.2"},
    {"кардридер", "кард-ридер", "card reader", "карт памяти", "microsd", "sd"},
    {"poe", "802.3af", "802.3at", "poe+"},
    {"sfp+", "10gbase", "10g"},
    {"windows"},
    {"linux", "astra", "альт", "ред ос", "red os", "основа", "эльбрус"},
    {"usb-a", "type-a", "usb a"},
    {"лазерный источник", "laser phosphor", "лазер"},
    {"накладн", "on-ear"},
    {"полноразмерн", "over-ear"},
    {"вкладыш", "внутриканальн", "in-ear"},
]
for _fam in FAMILIES:
    VALUE_SYNONYMS.extend(_fam)
INTERFACE_GROUPS = VALUE_SYNONYMS[:13]
_FAMILY_OF = {}
for _fam in FAMILIES:
    for _g in _fam:
        _FAMILY_OF[id(_g)] = _fam


def norm_text(s: str) -> str:
    s = (s or "").lower().replace("ё", "е").replace(" ", " ")
    s = re.sub(r"\s+", " ", s)
    s = " ".join(_cyr_lat(w) if re.search(r"\d", w) and len(w) <= 5 else w for w in s.split(" "))
    return " " + s + " "


def _hit(text: str, group: set) -> bool:
    """Есть ли в тексте слово из группы. «управляемый» внутри «неуправляемый» не считается."""
    for g in group:
        if not g:
            continue
        start = 0
        while True:
            i = text.find(g, start)
            if i < 0:
                break
            if g.startswith("не") or text[max(0, i - 2):i] != "не":
                return True
            start = i + 1
    return False


def text_match(product_text: str, value: str, closed: bool = False) -> str:
    """Сравнить текстовое значение с описанием товара -> ok | fail | unknown."""
    p = norm_text(product_text)
    v = norm_text(value).strip()
    if not v:
        return "unknown"
    vv = " " + v + " "
    if v in p:
        return "ok"
    hit = [grp for grp in VALUE_SYNONYMS if _hit(vv, grp)]
    if hit and all(_hit(p, grp) for grp in hit):
        return "ok"
    # короткие коды (RAID 1, «5») — как отдельное слово
    if len(v) <= 3 and not hit:
        return "ok" if re.search(r"(?<![\w.])" + re.escape(v) + r"(?![\w.])", p) else ("fail" if closed else "unknown")
    # явное противоречие внутри семейства (цветная / ч/б, A3 / A4, встроенный / внешний…)
    for grp in hit:
        fam = _FAMILY_OF.get(id(grp))
        if fam and not _hit(p, grp) and any(_hit(p, g2) for g2 in fam if g2 is not grp):
            return "fail"
    words = [stem(w) for w in re.findall(r"[a-zа-я0-9+\-.]{3,}", v)]
    words = [w for w in words if w and w not in ("или", "для", "при", "без", "наличие")]
    if words:
        found = sum(w in p for w in words)
        need = len(words) if len(words) <= 2 else max(2, -(-2 * len(words) // 3))
        if found >= need:
            return "ok"
    if closed and any(grp in INTERFACE_GROUPS for grp in hit):
        return "fail"
    return "unknown"


def text_has(product_text: str, value: str) -> bool:
    return text_match(product_text, value) == "ok"


_END = re.compile(r"(ого|его|ему|ому|ыми|ими|ее|ие|ые|ое|ей|ий|ый|ой|ем|им|ым|ом|их|ых|ую|юю|ая|яя|ою|ею|ам|ям|ах|ях|ов|ев|а|я|ы|и|е|о|у|ю|ь)$")


def stem(w: str) -> str:
    if re.search(r"\d", w) or len(w) <= 4:
        return w
    s = _END.sub("", w)
    return s if len(s) >= 3 else w


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


def _tol(dim: str | None, factor: float = 1.0) -> float:
    # ГБ/ТБ и «тыс.» (1000 или 1024) — допуск 2,5 %, остальное — 0,5 % на округление
    return 0.025 if dim == "data" or (dim == "count" and factor >= 1000) else 0.005


# текстовые столбцы, где непустое значение само означает «есть»
PRESENCE_TEXT_KEYS = {"wifi", "bluetooth", "hs_mic", "noise_cancel", "ports_text", "video_inputs", "connection"}
# числовые столбцы-«количества»: «есть» = больше нуля
COUNT_KEYS = {"hdmi", "dp", "vga", "dvi", "usb_c", "usb3", "usb3a", "usb3c", "usb2", "usb_any", "usb_gen2", "rj45", "webcam",
              "adf", "ports_rj45", "ports_sfp", "ports_sfp10", "ports_poe", "ports_combo", "eth_ports", "sip", "ups_outlets",
              "vlan", "battery_wh", "display_in", "screen", "speakers", "tray_in", "tray_out", "card_reader"}

ENERGY = ["g", "f", "e", "d", "c", "b", "a", "a+", "a++", "a+++"]


def _energy_rank(s: str) -> int | None:
    m = re.search(r"\b([a-gа-г])\s*(\+{0,3})", norm_text(s).replace("а", "a"))
    if not m:
        return None
    k = m.group(1).replace("а", "a") + m.group(2)
    return ENERGY.index(k) if k in ENERGY else None


def compare(req: Requirement, have_raw, have_unit: str | None = None, kind: str = "", key: str = "",
            closed: bool = False) -> tuple[str, str]:
    """Проверить значение товара. -> (ok|fail|unknown, текст значения товара).

    kind — тип столбца каталога (num/text/bool/res); при несовпадении типа требования и столбца
    честно возвращаем «нет данных», а не «не подходит»."""
    if have_raw is None:
        return "unknown", ""
    have = str(have_raw).strip()
    if have == "" or have.lower() == "nan":
        return "unknown", ""
    shown = have + (f" {have_unit}" if have_unit and not re.search(r"[a-zа-я]", have.lower()) else "")
    is_num_req = req.op in (">=", "<=", "диапазон") or (req.op == "=" and req.vmin is not None and not req.values)
    yesno = bool(req.values) and len(req.values) == 1 and req.values[0] in ("да", "нет")

    if key == "vesa":
        need = re.findall(r"(\d{2,3})\s*[xх×*]\s*(\d{2,3})", " ".join(req.values) or req.raw)
        got = re.findall(r"(\d{2,3})\s*[xх×*]\s*(\d{2,3})", have)
        if need and got:
            return ("ok" if any(n in got for n in need) else "fail"), shown
        if not need and yesno:
            pass
        elif need:
            return "unknown", shown
    if key == "energy_class":
        rq, rh = _energy_rank(" ".join(req.values) or req.raw), _energy_rank(have)
        if rq is None or rh is None:
            return "unknown", shown
        if re.search(r"не ниже|не хуже|≥|>=", (req.raw or "").lower()) or req.op == ">=":
            return ("ok" if rh >= rq else "fail"), shown
        return ("ok" if rh == rq else "fail"), shown
    if kind == "text" and is_num_req and not numbers_in(have):
        return "unknown", shown
    if kind in ("text",) and is_num_req and key not in ("ups_in_voltage",):
        # в текстовом описании числа могут относиться к другому — не судим
        if key in ("lamp_life", "throw", "cpu_cores", "duty", "poe_budget"):
            pass
        else:
            return "unknown", shown
    if kind == "num" and not is_num_req and not yesno and not (req.unit == "пиксель"):
        return "unknown", shown
    if kind == "bool" and not yesno and not is_num_req:
        return "unknown", shown

    # разрешение
    if req.unit == "пиксель" and req.values and RES_RE.search(req.values[0]):
        need = RES_RE.search(req.values[0])
        got = RES_RE.search(have)
        if not got:
            return "unknown", shown
        nw, nh = int(need.group(1)), int(need.group(2))
        gw, gh = int(got.group(1)), int(got.group(2))
        op = ">=" if key == "proj_supported_res" else req.op   # «поддерживает до» — достаточно не меньше
        if op == ">=":
            ok = max(gw, gh) >= max(nw, nh) and min(gw, gh) >= min(nw, nh)
        elif op == "<=":
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
        tol = _tol(lk[0] if lk else None, lk[1] if lk else 1.0)
        if req.op == ">=":
            v = max(conv)
            ok = v > req.vmin if req.min_strict else v >= req.vmin * (1 - tol)
            if not ok and re.match(r"^\s*(от|from)\s", have.lower()):
                return "unknown", shown + " (в каталоге только нижняя граница)"
        elif req.op == "<=":
            v = min(conv)
            ok = v < req.vmax if req.max_strict else v <= req.vmax * (1 + tol)
        elif req.op == "диапазон":
            ok = any(req.vmin * (1 - tol) <= v <= req.vmax * (1 + tol) for v in conv)
            rng = re.search(r"\d\s*[–—-]\s*\d", have)
            if not ok and rng and len(conv) >= 2:
                lo, hi = min(conv), max(conv)
                ok = lo <= req.vmax and hi >= req.vmin   # диапазон товара перекрывает требуемый
        else:
            ok = any(abs(v - req.vmin) <= abs(req.vmin) * tol + 1e-9 for v in conv)
            if not ok and len(conv) >= 2 and re.search(r"\d\s*[–—-]\s*\d", have):
                ok = min(conv) <= req.vmin <= max(conv)      # «= 50 Гц» при диапазоне товара 45–65 Гц
        return ("ok" if ok else "fail"), shown

    # да / нет
    if yesno and kind == "text" and key not in PRESENCE_TEXT_KEYS:
        # «Поддержка DHCP-сервера: да» — ищем саму функцию в описании, а не просто непустую ячейку
        toks = [t.lower().rstrip("-") for t in re.findall(r"[A-Za-z][A-Za-z0-9.+\-]{1,}", req.name)]
        toks = [t for t in toks if len(t) >= 2]
        hl = have.lower()
        if toks and all(t in hl for t in toks):
            return ("ok" if req.values[0] == "да" else "fail"), shown
        return "unknown", shown
    if yesno and kind == "num" and key and key not in COUNT_KEYS:
        return "unknown", shown
    if yesno:
        hl = have.lower()
        want = req.values[0] == "да"
        if want and re.search(r"опци", hl):
            return "ok", shown + " — опция, заказать"
        if not want and re.search(r"\bбез\b|или без|опци", hl):
            return "ok", shown
        tv = truthy(have)
        if tv is None:
            return "unknown", shown
        return ("ok" if tv == want else "fail"), shown

    # текстовые значения
    vals = req.values or ([req.value] if req.value else [])
    if not vals:
        return "unknown", shown
    res = [text_match(have, v, closed) for v in vals]
    if req.all_values:
        if all(r == "ok" for r in res):
            return "ok", shown
        if any(r == "fail" for r in res):
            return "fail", shown
        return "unknown", shown
    if any(r == "ok" for r in res):
        return "ok", shown
    if all(r == "fail" for r in res) and req.op != "текст":
        return "fail", shown
    return "unknown", shown
