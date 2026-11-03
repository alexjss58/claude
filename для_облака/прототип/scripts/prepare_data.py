"""Подготовка демо-данных для прототипа «Тендер под ключ» из выгрузок Тендерплана.

Что делает скрипт:
1. Читает лист «Завершенные закупки» из четырёх выгрузок Тендерплана (ноябрь 2026):
   (11) связь и аудио-видео 26.3/26.4, 44-ФЗ и 223-ФЗ, 02.08–01.11.2026;
   (4)  связь и аудио-видео 26.3/26.4, только 223-ФЗ, последние 1000 записей;
   (10) приборы 26.51, 44-ФЗ и 223-ФЗ, 02.08–01.11.2026;
   (5)  приборы 26.51, только 223-ФЗ, последние 1000 записей.
   Заголовки во 2-й строке (header=1), первая колонка — стрелка-ссылка, её отбрасываем.
2. Отсеивает всё, что не похоже на «чистую поставку товара»: монтаж, работы, услуги,
   ремонт, обслуживание, поверка и т. п. Правила — по названию закупки (свои, первый круг F).
   Дополнительно отсеивает явно чужие для пилота товары (канцтовары, хозтовары, мебель...).
3. Считает бейджи «под своего?», «нацрежим», «мало конкурентов» и историю заказчика.
4. Считает медианы снижения цены: ниша × закон × способ × число участников
   (формат «H → F» из ПОТОКИ.md) — это наша оценка, пока нет файла цена/для_демо.json.
5. Собирает сводку рынка из листа «Анализ» и из строк выгрузки.

Выход (в папку прототипа):
  src/data/tenders.json        — 150–300 закупок для демо-кабинета;
  src/data/price_table_own.json — таблица снижения цены (оценка по данным);
  src/data/market.json         — цифры рынка для лендинга.

Запуск:  python3 scripts/prepare_data.py   (из папки прототип/)
Исходные файлы в данные/ не меняются.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]  # .../для_облака
SRC_DIR = ROOT / "данные" / "выгрузки_тендерплан"
OUT_DIR = Path(__file__).resolve().parents[1] / "src" / "data"

FILES = {
    "(11)": ("svyaz", "Связь и аудио-видео (ОКПД2 26.3, 26.4)"),
    "(4)": ("svyaz", "Связь и аудио-видео (ОКПД2 26.3, 26.4)"),
    "(10)": ("pribory", "Приборы (ОКПД2 26.51)"),
    "(5)": ("pribory", "Приборы (ОКПД2 26.51)"),
}
NICHE_SHORT = {"svyaz": "Связь и аудио-видео", "pribory": "Приборы"}

SOURCE_NOTE = "по данным Тендерплана, ноябрь 2026, оценка"

# ---------------------------------------------------------------------------
# 1. Правила «чистая поставка или работы/услуги» (по названию закупки)
# ---------------------------------------------------------------------------

# Признаки работ и услуг. Если найден хоть один — это не «чистая поставка».
WORKS_RE = re.compile(
    r"монтаж|демонтаж|пуско-?налад|наладк|установк|выполнени[ея]\s+работ|\bработ[ыа]?\b|"
    r"услуг|оказани|ремонт|обслуживан|\bто\b|сервисн|поверк|калибровк|аттестаци|"
    r"проектир|строител|реконструкц|модернизац|капитальн|разработк|внедрени|создани[ея]|"
    r"аренд|прокат|подключени|настройк|инсталляц|сопровожден|техническ\w*\s+поддержк|"
    r"обучени|проведени[ея]|изготовлени|производств|сборк|смр|пир\b|под\s+ключ",
    re.IGNORECASE,
)

# Явно не наши товары (для пилота оргтехники/связи/приборов): отсекаем, чтобы демо было «про дело».
OFFTOPIC_RE = re.compile(
    r"канцел|хозяйств|хозтовар|моющ|мебел|продукт\w*\s+питани|пищев|строительн\w*\s+материал|"
    r"подар|сувенир|спецодежд|обув|текстил|лекарств|медикамент|реактив|ручн\w*\s+инструмент|"
    r"товар\w*\s+общего\s+спроса|кейс|"
    r"запасн\w*\s+част\w*\s+к\s+медицин|медицинск|автомобил|автозапчаст|шин[ыа]?\b|"
    r"топлив|бензин|электротовар|светильник|ламп|кондиционер|сплит|бытов\w*\s+техник|"
    r"пожаротуш|огнетуш|металлодетектор|досмотров|посуд|книг|учебн\w*\s+литератур|"
    r"брендирован|электроматериал|элетроматериал|кабел",
    re.IGNORECASE,
)

# Ключевые слова, по которым закупка «про» нишу (нужен хотя бы один, если название не общее).
NICHE_KEYS = {
    "svyaz": re.compile(
        r"телефон|радиостанц|раци[йияю]|радиосистем|связ|коммутатор|маршрутизатор|сетев|"
        r"видеонаблюд|видеокамер|камер|телевизор|монитор|проектор|экран|акустич|колонк|"
        r"микрофон|микшер|пульт|усилител|звук|аудио|видео|гарнитур|наушник|документ-?камер|"
        r"громкоговорит|оповещ|компьютер|ноутбук|моноблок|оргтехник|бесперебойн|ибп|"
        r"принтер|мфу|сервер|планшет|интерактивн|панел|антенн|оптическ|трансивер|"
        r"патч-?корд|sfp|медиаконвертер|\bip\b|атс|радио|домофон|видеостен|"
        r"вычислительн|периферийн|комплектующ|терминал|шлюз|спутник|навигац|"
        r"конференц|видеоконференц|веб-?камер|рабоч\w*\s+станц|системн\w*\s+блок",
        re.IGNORECASE,
    ),
    "pribory": re.compile(
        r"прибор|измерит|анализатор|термометр|манометр|генератор|осциллограф|мультиметр|"
        r"тестер|спектрометр|спектрофотометр|хроматограф|ph-?метр|рн-?метр|кондуктометр|"
        r"датчик|преобразовател|счетчик|счётчик|расходомер|газоанализатор|дозиметр|"
        r"радиометр|тепловизор|термостат|калибратор|регистратор|влагомер|твердомер|"
        r"толщиномер|дефектоскоп|сигнализатор|климатическ|испытательн|гигрометр|"
        r"барометр|метеостанц|нивелир|теодолит|геодезич|тахеометр|лабораторн\w*\s+оборуд|"
        r"весы|вольтметр|амперметр|мегаомметр|частотомер|рефрактометр|вискозиметр|"
        r"титратор|фотометр|люксметр|шумомер|виброметр|пирометр|секундомер|штангенциркул|"
        r"микрометр|индикатор|контроллер|термогигрометр|логгер|эталон|стенд",
        re.IGNORECASE,
    ),
}

# Общие названия («Поставка товара», «Поставка оборудования») — оставляем, ниша известна по ОКПД2.
GENERIC_RE = re.compile(r"^\s*(поставк\w*|приобретени\w*|закупк\w*)\s+(товар\w*|оборудовани\w*)", re.IGNORECASE)

# ---------------------------------------------------------------------------
# 2. Бейджи
# ---------------------------------------------------------------------------

# Бренды и торговые марки, которые встречаются в названиях закупок связи, аудио-видео и приборов.
BRANDS = [
    "Cisco", "Huawei", "Yealink", "Panasonic", "NEC", "Avaya", "Samsung", "LG", "Sony", "Shure",
    "Sennheiser", "Behringer", "Yamaha", "Hikvision", "Dahua", "Polycom", "Logitech", "HP",
    "Kyocera", "Canon", "Xerox", "Eltex", "Элтекс", "Fluke", "Keysight", "Rohde", "Testo",
    "ОВЕН", "Kangbo", "Motorola", "Hytera", "Kenwood", "Icom", "Vertex", "Epson", "BenQ",
    "Mikrotik", "MikroTik", "Juniper", "Zyxel", "D-Link", "TP-Link", "Grandstream", "Fanvil",
    "Jabra", "Plantronics", "Poly", "Bose", "JBL", "Crown", "Extron", "Crestron", "Kramer",
    "Lenovo", "Dell", "Apple", "iPad", "Acer", "Asus", "Aquarius", "Гравитон", "Graviton",
    "Yadro", "Ядро", "Mettler", "Sartorius", "Ohaus", "Shimadzu", "Agilent", "Thermo", "Hach",
    "Метран", "Элемер", "ЭЛЕМЕР", "Теплоприбор", "Rigol", "Tektronix", "Актаком", "АКИП",
    "Testo", "Siemens", "Schneider", "Honeywell", "Emerson", "Endress", "Vega", "Bosch",
    "Соматос", "Netgear", "Ubiquiti", "Ruckus", "Aruba", "Qtech", "QTECH", "Snr", "SNR",
]
BRAND_RE = re.compile(r"(?<![\w-])(" + "|".join(re.escape(b) for b in BRANDS) + r")(?![\w-])")
# Модель вида «SV8300», «KB2277», «DP1400»: латиница + цифры (не путать с номерами закупок).
MODEL_RE = re.compile(r"(?<![\w/.-])[A-Za-z]{1,4}-?\d{2,5}[A-Za-z]{0,3}(?![\w/.-])")
EQUIV_RE = re.compile(r"эквивалент", re.IGNORECASE)

# Группы товаров, для которых обычно нужно проверять национальный режим (ПП РФ № 1875).
# Это только подсказка «проверить», не вывод о запрете. Не юридическая консультация.
NATREG_RE = re.compile(
    r"компьютер|ноутбук|моноблок|планшет|сервер|системн\w*\s+блок|рабоч\w*\s+станц|"
    r"монитор|принтер|мфу|оргтехник|вычислительн|коммутатор|маршрутизатор|сетев|"
    r"телефон|радиостанц|раци|связ|видеокамер|видеонаблюд|телевизор|проектор|"
    r"панел|ибп|бесперебойн|хранени\w*\s+данн|терминал|шлюз|атс|радиоэлектрон|"
    r"измерит|прибор|анализатор|счетчик|счётчик|датчик|термометр|манометр|"
    r"осциллограф|мультиметр|генератор",
    re.IGNORECASE,
)


def clean_num(v):
    if v is None:
        return None
    if isinstance(v, str):
        v = v.strip().replace("\xa0", "").replace(" ", "").replace(",", ".")
        if v in ("", "-", "—"):
            return None
        try:
            return float(v)
        except ValueError:
            return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if pd.isna(f):
        return None
    return f


def method_short(m: str) -> str:
    m = (m or "").lower()
    if "аукцион" in m:
        return "Электронный аукцион"
    if "котиров" in m:
        return "Запрос котировок"
    if "запрос цен" in m:
        return "Запрос цен"
    if "предложен" in m:
        return "Запрос предложений"
    if "конкурс" in m:
        return "Конкурс"
    return "Иной способ"


def participants_bucket(n):
    if n is None:
        return None
    n = int(n)
    if n <= 1:
        return "1"
    if n == 2:
        return "2"
    if n == 3:
        return "3"
    return "4+"


def load() -> pd.DataFrame:
    frames = []
    for tag, (niche, niche_name) in FILES.items():
        path = SRC_DIR / f"Анализ выборки 03.11.2026 {tag}.xlsx"
        df = pd.read_excel(path, sheet_name="Завершенные закупки", header=1)
        df = df.iloc[:, 1:]  # первая колонка — стрелка-ссылка
        df = df[df["Предмет закупки"].notna() & df["Закон"].notna()].copy()
        df["ниша"] = niche
        df["файл"] = tag
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    for c in ["НМЦ", "Обеспечение заявки", "Обеспечение контракта", "Падения цены, %",
              "Кол-во участников", "Цена победителя"]:
        df[c] = df[c].map(clean_num)
    # Если «Падения цены» нет, но есть НМЦ и цена победителя — считаем снижение сами.
    def fill_drop(r):
        v = r["Падения цены, %"]
        if v is not None and not pd.isna(v):
            return v
        nmc, win = r["НМЦ"], r["Цена победителя"]
        if nmc and win and not pd.isna(nmc) and not pd.isna(win) and 0 < win <= nmc:
            return round((1 - win / nmc) * 100, 2)
        return None
    df["Падения цены, %"] = df.apply(fill_drop, axis=1).astype(object)
    df["ИНН Заказчика"] = df["ИНН Заказчика"].map(
        lambda v: str(int(v)) if clean_num(v) is not None else "")
    df["Предмет закупки"] = (df["Предмет закупки"].astype(str).str.replace("_x000D_", " ", regex=False)
                            .str.replace(r"\s+", " ", regex=True).str.strip())
    # Пустые числа держим как None (а не NaN), чтобы проверки «is not None» работали честно.
    for c in ["НМЦ", "Обеспечение заявки", "Обеспечение контракта", "Падения цены, %",
              "Кол-во участников", "Цена победителя"]:
        df[c] = df[c].astype(object).where(df[c].notna(), None)
    # Файлы (11) и (4), (10) и (5) пересекаются по 223-ФЗ за октябрь — убираем дубли.
    before = len(df)
    df = df.drop_duplicates(subset=["Предмет закупки", "Заказчик", "НМЦ", "Дата окончания", "ниша"])
    print(f"Строк всего: {before}, после удаления дублей: {len(df)}")
    return df


def classify(df: pd.DataFrame) -> pd.DataFrame:
    name = df["Предмет закупки"]
    df["работы_услуги"] = name.str.contains(WORKS_RE)
    df["не_наш_товар"] = name.str.contains(OFFTOPIC_RE)

    def niche_ok(row):
        n = row["Предмет закупки"]
        return bool(NICHE_KEYS[row["ниша"]].search(n)) or bool(GENERIC_RE.search(n))

    df["про_нишу"] = df.apply(niche_ok, axis=1)
    df["чистая_поставка"] = ~df["работы_услуги"] & ~df["не_наш_товар"] & df["про_нишу"]
    return df


def drop_ok(v):
    # Падение больше 90% почти всегда означает цену за единицу вместо цены контракта — в статистику не берём.
    return v is not None and 0 <= v <= 90


def customer_history(df: pd.DataFrame) -> dict:
    hist = {}
    for inn, g in df[df["ИНН Заказчика"] != ""].groupby("ИНН Заказчика"):
        drops = [v for v in g["Падения цены, %"] if drop_ok(v)]
        parts = [v for v in g["Кол-во участников"] if v is not None]
        hist[inn] = {
            "закупок_в_выгрузке": int(len(g)),
            "медиана_снижения_%": round(float(pd.Series(drops).median()), 1) if drops else None,
            "медиана_участников": float(pd.Series(parts).median()) if parts else None,
            "доля_с_одним_участником_%": round(100 * sum(1 for p in parts if p <= 1) / len(parts)) if parts else None,
            "без_снижения": int(sum(1 for v in drops if v < 0.5)),
            "n_со_снижением": len(drops),
        }
    return hist


def badges(row, hist) -> list[dict]:
    out = []
    name = row["Предмет закупки"]
    brand = BRAND_RE.search(name)
    model = MODEL_RE.search(name)
    equiv = bool(EQUIV_RE.search(name))
    h = hist.get(row["ИНН Заказчика"]) or {}
    lazy = (h.get("n_со_снижением", 0) >= 2 and h.get("без_снижения", 0) >= 2
            and (h.get("доля_с_одним_участником_%") or 0) >= 60)
    reasons = []
    if brand:
        reasons.append(f"в названии марка «{brand.group(1)}»")
    if model and not brand:
        reasons.append(f"в названии модель «{model.group(0)}»")
    if (brand or model) and not equiv:
        reasons.append("нет слов «или эквивалент»")
    if lazy:
        reasons.append("у заказчика часто один участник и цена без снижения")
    if reasons and (brand or model or lazy):
        out.append({"код": "svoy", "текст": "под своего?", "почему": "; ".join(reasons)})
    if NATREG_RE.search(name) or GENERIC_RE.search(name):
        out.append({"код": "natreg", "текст": "нацрежим",
                    "почему": "группа товаров, где обычно действует нацрежим (ПП РФ № 1875) — проверить по извещению"})
    n = row["Кол-во участников"]
    hp = h.get("медиана_участников")
    if (n is not None and n <= 1) or (hp is not None and hp <= 1.5 and h.get("закупок_в_выгрузке", 0) >= 2):
        why = f"участников в этой закупке: {int(n)}" if n is not None else ""
        if hp is not None:
            why = (why + "; " if why else "") + f"медиана у заказчика: {hp:g}"
        out.append({"код": "few", "текст": "мало конкурентов", "почему": why})
    return out


def risks(row) -> list[str]:
    r = []
    name = row["Предмет закупки"]
    nmc = row["НМЦ"]
    if BRAND_RE.search(name) and not EQUIV_RE.search(name):
        r.append("Марка в названии без «или эквивалент»: возможна закупка под конкретного поставщика.")
    ob_k, ob_z = row["Обеспечение контракта"], row["Обеспечение заявки"]
    if nmc and ob_k and ob_k / nmc >= 0.1:
        r.append(f"Большое обеспечение контракта: {ob_k / nmc * 100:.0f}% от НМЦ — нужна банковская гарантия или свободные деньги.")
    elif ob_k:
        r.append(f"Обеспечение контракта {ob_k:,.0f} ₽ — заложить в план денег.".replace(",", " "))
    if nmc and ob_z and ob_z / nmc >= 0.01:
        r.append(f"Обеспечение заявки {ob_z:,.0f} ₽ — деньги на спецсчёте до итогов.".replace(",", " "))
    if row["способ"] in ("Запрос котировок", "Запрос цен"):
        r.append("Котировки и запросы цен идут быстро: на подачу обычно несколько дней.")
    if row["Кол-во участников"] is not None and row["Кол-во участников"] >= 5:
        r.append(f"Много участников ({int(row['Кол-во участников'])}): жди сильного снижения цены.")
    return r


def price_table(df: pd.DataFrame) -> list[dict]:
    rows = []
    d = df[df["чистая_поставка"] & df["Падения цены, %"].map(drop_ok) & df["Кол-во участников"].notna()].copy()
    d["участников"] = d["Кол-во участников"].map(participants_bucket)

    def add(g, ниша, закон, способ, участников):
        s = g["Падения цены, %"].astype(float)
        if len(s) < 5:
            return
        rows.append({
            "ниша": ниша, "закон": закон, "способ": способ, "участников": участников,
            "медиана_снижения_%": round(float(s.median()), 1),
            "p25_%": round(float(s.quantile(0.25)), 1),
            "p75_%": round(float(s.quantile(0.75)), 1),
            "n": int(len(s)),
        })

    for (niche, law, method, pb), g in d.groupby(["ниша", "Закон", "способ", "участников"]):
        add(g, NICHE_SHORT[niche], law, method, pb)
    # Агрегаты «любой способ / любое число участников» — запасной вариант, когда точной ячейки нет.
    for (niche, law, pb), g in d.groupby(["ниша", "Закон", "участников"]):
        add(g, NICHE_SHORT[niche], law, "все способы", pb)
    for (niche, law), g in d.groupby(["ниша", "Закон"]):
        add(g, NICHE_SHORT[niche], law, "все способы", "все")
    return rows


def market(df: pd.DataFrame) -> dict:
    """Цифры рынка: шапка листа «Анализ» (файлы 11 и 10) + расчёт по строкам выгрузки."""
    out = {"подпись": SOURCE_NOTE, "ниши": []}
    for tag, key in (("(11)", "svyaz"), ("(10)", "pribory")):
        a = pd.read_excel(SRC_DIR / f"Анализ выборки 03.11.2026 {tag}.xlsx", sheet_name="Анализ", header=None, nrows=32)
        cells = {}
        for _, row in a.iterrows():
            vals = [v for v in row.tolist() if not (isinstance(v, float) and pd.isna(v))]
            for i, v in enumerate(vals[:-1]):
                if isinstance(vals[i + 1], str):
                    cells[vals[i + 1]] = v
        period = None
        for _, row in a.iterrows():
            for v in row.tolist():
                if isinstance(v, str) and v.startswith("С ") and " по " in v:
                    period = v
        total_sum = next((k for k in cells if str(k).startswith("Тендеров на сумму")), "")
        sub = df[df["ниша"] == key]
        clean = sub[sub["чистая_поставка"]]
        parts = [v for v in sub["Кол-во участников"] if v is not None]
        drops = [v for v in sub["Падения цены, %"] if drop_ok(v)]
        nmc = [v for v in clean["НМЦ"] if v]
        out["ниши"].append({
            "код": key,
            "название": FILES[tag][1],
            "период": period,
            "закупок_за_период": int(cells.get(total_sum, 0)) if total_sum else None,
            "сумма_за_период": total_sum.replace("Тендеров на сумму ", "").replace(", ₽", " ₽") if total_sum else None,
            "среднее_снижение_%": cells.get("Среднее падение цены"),
            "среднее_участников": cells.get("Среднее количество участников"),
            "медиана_снижения_%_выгрузка": round(float(pd.Series(drops).median()), 1) if drops else None,
            "доля_с_одним_участником_%_выгрузка": round(100 * sum(1 for p in parts if p <= 1) / len(parts)) if parts else None,
            "доля_чистой_поставки_%_выгрузка": round(100 * len(clean) / len(sub)),
            "медиана_нмц_чистой_поставки": round(float(pd.Series(nmc).median())) if nmc else None,
            "строк_в_выгрузке": int(len(sub)),
        })
    return out


def nn(v):
    """NaN и бесконечности в JSON недопустимы — превращаем в null, числа округляем до копеек."""
    if v is None:
        return None
    if isinstance(v, float):
        if pd.isna(v) or v in (float("inf"), float("-inf")):
            return None
        return round(v, 2)
    return v


def deep_clean(o):
    """Рекурсивно убирает NaN из словарей и списков (например, пустой регион)."""
    if isinstance(o, dict):
        return {k: deep_clean(v) for k, v in o.items()}
    if isinstance(o, list):
        return [deep_clean(v) for v in o]
    return nn(o)


def stable_id(row) -> str:
    key = f"{row['Предмет закупки']}|{row['Заказчик']}|{row['НМЦ']}|{row['Дата окончания']}"
    return "T" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:8]


def main():
    df = load()
    df["способ"] = df["Тип проведения"].map(method_short)
    df = classify(df)

    print("Чистая поставка:", int(df["чистая_поставка"].sum()), "из", len(df))
    print(df.groupby("ниша")["чистая_поставка"].mean().round(2).to_dict())

    hist = customer_history(df)
    pt = price_table(df)

    # Отбор для демо: чистая поставка, НМЦ известна, размещение не отменено.
    good_status = df["Статус"].isin(["Размещение завершено", "Исполнение", "Исполнение завершено", "Работа комиссии"])
    cand = df[df["чистая_поставка"] & df["НМЦ"].notna() & (df["НМЦ"] > 0) & good_status].copy()
    cand["есть_итог"] = cand["Кол-во участников"].notna()
    # Немного приоритета закупкам с известным итогом — на них видно цену.
    cand = cand.sample(frac=1.0, random_state=7)
    cand = cand.sort_values("есть_итог", ascending=False, kind="stable")
    cand["_svoy"] = cand.apply(lambda r: any(b["код"] == "svoy" for b in badges(r, hist)), axis=1)
    cand = cand.sort_values(["_svoy", "есть_итог"], ascending=False, kind="stable")
    take = {("svyaz", "44-ФЗ"): 75, ("svyaz", "223-ФЗ"): 75, ("pribory", "44-ФЗ"): 55, ("pribory", "223-ФЗ"): 55}
    picked = pd.concat([cand[(cand["ниша"] == k) & (cand["Закон"] == law)].head(n) for (k, law), n in take.items()])
    picked["_d"] = pd.to_datetime(picked["Дата окончания"], format="%d.%m.%Y", errors="coerce")
    picked = picked.sort_values("_d", ascending=False)

    tenders = []
    for _, r in picked.iterrows():
        h = hist.get(r["ИНН Заказчика"])
        tenders.append({
            "id": stable_id(r),
            "предмет": r["Предмет закупки"],
            "ниша": r["ниша"],
            "закон": r["Закон"],
            "способ": r["способ"],
            "способ_полностью": r["Тип проведения"],
            "статус": r["Статус"],
            "нмц": nn(r["НМЦ"]),
            "обеспечение_заявки": nn(r["Обеспечение заявки"]),
            "обеспечение_контракта": nn(r["Обеспечение контракта"]),
            "регион": r["Регион"],
            "дата_окончания": r["Дата окончания"],
            "снижение_%": round(r["Падения цены, %"], 1) if drop_ok(r["Падения цены, %"]) else None,
            "участников": int(r["Кол-во участников"]) if r["Кол-во участников"] is not None else None,
            "цена_победителя": nn(r["Цена победителя"]),
            "заказчик": r["Заказчик"],
            "инн_заказчика": r["ИНН Заказчика"],
            "история_заказчика": h,
            "бейджи": badges(r, hist),
            "риски": risks(r),
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    meta = {
        "источник": "Тендерплан, выгрузки «Анализ выборки 03.11.2026» (11), (4), (10), (5), лист «Завершенные закупки»",
        "подпись": SOURCE_NOTE,
        "что_это": "Завершённые закупки августа–октября 2026. В рабочей версии здесь будут актуальные закупки.",
        "снижение": "Если в выгрузке нет процента снижения, считаем его по цене победителя и НМЦ.",
        "правила_отбора": "Оставлена «чистая поставка»: по названию отсеяны монтаж, работы, услуги, ремонт, обслуживание, поверка; "
                          "отсеяны чужие для пилота товары (канцтовары, хозтовары, мебель, медицина и т. п.).",
        "всего_строк": int(len(df)),
        "чистая_поставка_строк": int(df["чистая_поставка"].sum()),
    }
    (OUT_DIR / "tenders.json").write_text(
        json.dumps(deep_clean({"meta": meta, "закупки": tenders}), ensure_ascii=False, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    (OUT_DIR / "price_table_own.json").write_text(json.dumps(pt, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT_DIR / "market.json").write_text(json.dumps(market(df), ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"Закупок в демо: {len(tenders)}  (связь: {sum(t['ниша'] == 'svyaz' for t in tenders)}, "
          f"приборы: {sum(t['ниша'] == 'pribory' for t in tenders)})")
    print(f"Строк в таблице цены: {len(pt)}")
    # Контроль качества фильтра: 25 отсеянных и 25 оставленных названий
    rej = df[~df["чистая_поставка"]].sample(25, random_state=3)["Предмет закупки"].str[:100].tolist()
    acc = picked.sample(25, random_state=3)["Предмет закупки"].str[:100].tolist()
    print("\n--- ОТСЕЯНО (пример) ---\n" + "\n".join(rej))
    print("\n--- ОСТАВЛЕНО (пример) ---\n" + "\n".join(acc))


if __name__ == "__main__":
    main()
