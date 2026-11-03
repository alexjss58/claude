"""Загрузка каталога поставщика (xlsx/csv) и разбор столбцов.

Столбцы распознаются по заголовку: сначала точное совпадение с нашим шаблоном
(каталог_демо.xlsx), затем по тем же правилам, что и характеристики техзадания
(«ОЗУ, Гб», «Объём SSD» и т. п.). Так можно загрузить и свой прайс.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from . import units
from .synonyms import CATEGORIES, KEY_BY_NAME, KEYS, detect_category, map_key, norm_name

META_COLS = {
    "sku": [r"артикул", r"^код", r"sku", r"part ?number"],
    "category": [r"категори", r"тип товара", r"группа", r"вид товара"],
    "vendor": [r"производител", r"бренд", r"марка", r"vendor"],
    "model": [r"модель", r"наименование", r"товар$", r"название"],
    "config": [r"конфигурац", r"примечани"],
    "registry": [r"реестр"],
    "url": [r"источник", r"url", r"ссылка"],
    "price": [r"цена", r"стоимость", r"price"],
}

HEADER_TO_KEY = {k.header: k.key for k in KEYS}


def _read(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in (".xlsx", ".xlsm", ".xls"):
        xl = pd.ExcelFile(path)
        sheet = "каталог" if "каталог" in xl.sheet_names else xl.sheet_names[0]
        raw = pd.read_excel(xl, sheet, header=None, dtype=str)
    else:
        raw = None
        for enc in ("utf-8-sig", "cp1251"):
            try:
                first = path.read_bytes().decode(enc).splitlines()[0]
            except (UnicodeDecodeError, IndexError):
                continue
            # разделитель — тот, которого в строке заголовков больше всего (в заголовках бывают запятые: «ОЗУ, Гб»)
            sep = max([";", "\t", ","], key=first.count)
            try:
                raw = pd.read_csv(path, header=None, dtype=str, encoding=enc, sep=sep)
                break
            except Exception:
                continue
        if raw is None:
            raise ValueError(f"не удалось прочитать {path}")
    # строка заголовков — первая, где есть «модель/наименование»
    hdr = 0
    for i in range(min(10, len(raw))):
        row = " ".join(str(x).lower() for x in raw.iloc[i].tolist())
        if re.search(r"модель|наименование|артикул", row):
            hdr = i
            break
    df = raw.iloc[hdr + 1:].copy()
    df.columns = [str(c).strip() for c in raw.iloc[hdr].tolist()]
    df = df.dropna(how="all")
    return df


def map_columns(columns: list[str], sample_category: str | None = None) -> dict[str, str]:
    """Заголовок столбца -> ключ (мета-поле или характеристика)."""
    out: dict[str, str] = {}
    for c in columns:
        if c in HEADER_TO_KEY:
            out[c] = HEADER_TO_KEY[c]
            continue
        n = norm_name(c)
        hit = None
        for key, pats in META_COLS.items():
            if any(re.search(p, n) for p in pats):
                hit = "_" + key
                break
        if hit and hit not in out.values():
            out[c] = hit
            continue
        name_wo_unit = re.sub(r",\s*[^,]+$", "", c)
        for cat in ([sample_category] if sample_category else []) + CATEGORIES:
            k = map_key(name_wo_unit, cat) or map_key(c, cat)
            if k:
                out[c] = k.key
                break
    return out


class Catalog:
    def __init__(self, products: list[dict], colmap: dict[str, str], path: str = ""):
        self.products = products
        self.colmap = colmap
        self.path = path

    @classmethod
    def load(cls, path: str | Path) -> "Catalog":
        p = Path(path)
        df = _read(p)
        colmap = map_columns(list(df.columns))
        units_by_key = {}
        for col, key in colmap.items():
            if key.startswith("_"):
                continue
            u = units.unit_from_header(col)
            if not u and key in KEY_BY_NAME:
                u = KEY_BY_NAME[key].unit
            units_by_key[key] = u
        products = []
        for _, row in df.iterrows():
            prod: dict = {"_units": units_by_key}
            for col, key in colmap.items():
                v = row.get(col)
                if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() in ("", "nan"):
                    continue
                prod[key] = str(v).strip()
            if not prod.get("_model"):
                continue
            cat = (prod.get("_category") or "").strip().lower()
            if cat not in CATEGORIES:
                cat = detect_category(f"{cat} {prod.get('_model', '')}") or cat
            prod["_category"] = cat
            products.append(prod)
        return cls(products, colmap, str(p))

    def by_category(self, cat: str | None) -> list[dict]:
        if not cat:
            return []
        return [p for p in self.products if p.get("_category") == cat]

    def unit_of(self, key: str) -> str:
        if not self.products:
            return ""
        return self.products[0]["_units"].get(key, "")

    def columns_report(self) -> list[tuple[str, str]]:
        """Для показа «разбора столбцов» в демо-кабинете."""
        out = []
        for col, key in self.colmap.items():
            if key.startswith("_"):
                out.append((col, {"_sku": "артикул", "_category": "категория", "_vendor": "производитель",
                                  "_model": "модель", "_config": "примечание", "_registry": "реестр",
                                  "_url": "источник", "_price": "цена"}.get(key, key)))
            else:
                out.append((col, KEY_BY_NAME[key].header if key in KEY_BY_NAME else key))
        return out
