"""Сверка с каталогом и формат выхода «G → F» (ПОТОКИ.md)."""
import json
import os
import subprocess
import sys
from pathlib import Path

from tz_engine.catalog import Catalog
from tz_engine.eis import parse_notice_file
from tz_engine.matcher import match_purchase
from tz_engine.output import to_f

ROOT = Path(__file__).resolve().parents[1]
CAT = Catalog.load(ROOT / "каталог_демо.xlsx")


def test_catalog_loaded():
    assert 50 <= len(CAT.products) <= 100
    cats = {p["_category"] for p in CAT.products}
    assert {"ноутбук", "монитор", "мфу", "принтер", "коммутатор", "ip-телефон", "ибп", "проектор"} <= cats
    assert all(p.get("_url", "").startswith("http") for p in CAT.products)


def test_ups_nearest_with_schuko_mismatch():
    """Розетки Schuko нельзя «доконфигурировать» — статус «нет», но ближайший товар и причина показаны."""
    p = parse_notice_file(ROOT / "вход" / "eis" / "0820500000826005372.json")
    res = match_purchase(p, CAT)
    assert res[0].status == "нет"
    assert res[0].product["_sku"] == "IPN-BB650-EURO"
    fails = [c.req.name for c in res[0].fails]
    assert "Количество выходных розеток Schuko" in fails


def test_phones_for_panasonic_not_in_catalog():
    p = parse_notice_file(ROOT / "вход" / "eis" / "0252100003826000222.json")
    assert [m.status for m in match_purchase(p, CAT)] == ["нет", "нет"]


def test_configurable_mismatch_is_almost():
    """Не хватает ОЗУ (меняется конфигурацией) — «почти»; не та цветность — «нет»."""
    from tz_engine.conditions import parse_value
    from tz_engine.models import Position
    pos = Position(num=1, name="Ноутбук", ktru="26.20.11.110-00000139")
    pos.requirements = [parse_value("не менее 64 ГБ", "Общий объем установленной оперативной памяти"),
                        parse_value("не менее 15,6 дюйма", "Диагональ экрана")]
    from tz_engine.matcher import match_position
    m = match_position(pos, CAT)
    assert m.status == "почти"
    pos2 = Position(num=2, name="Принтер", ktru="26.20.16.120-00000101")
    pos2.requirements = [parse_value("Цветная", "Цветность")]
    assert match_position(pos2, CAT).status == "нет"


def test_held_out_vesa_and_ports():
    p = parse_notice_file(ROOT / "вход" / "eis_отложенная_проверка" / "0330300051226000293.json")
    m = match_purchase(p, CAT)[0]
    assert m.status == "нет" and "Стандарт крепления" in [c.req.name for c in m.fails]


def test_fits_example():
    p = parse_notice_file(ROOT / "вход" / "eis" / "0380200000126008404.json")
    res = match_purchase(p, CAT)
    printer = [m for pos, m in zip(p.positions, res) if pos.category == "принтер"][0]
    assert printer.status == "подходит"


REQ_TOP = {"закупка", "позиции", "итог", "режим"}
REQ_Z = {"номер", "предмет", "заказчик", "инн_заказчика", "закон", "способ", "нмц", "регион", "дата_окончания", "ссылка",
         "источник_документа"}
REQ_P = {"№", "наименование", "ктру", "окпд2", "количество", "единица", "характеристики", "сверка"}
REQ_C = {"имя", "условие", "значение", "единица", "эквивалент_допускается"}
REQ_S = {"статус", "товар_из_каталога", "артикул", "расхождения"}


def check_format(d: dict) -> None:
    assert REQ_TOP <= set(d)
    assert REQ_Z <= set(d["закупка"])
    assert d["режим"] in ("демо", "живой")
    assert set(d["итог"]) == {"подходит", "почти", "нет"}
    assert sum(d["итог"].values()) == len(d["позиции"])
    for p in d["позиции"]:
        assert REQ_P <= set(p)
        for c in p["характеристики"]:
            assert REQ_C <= set(c)
            assert c["условие"] in (">=", "<=", "=", "диапазон", "из_списка", "текст")
            assert isinstance(c["эквивалент_допускается"], bool)
        s = p["сверка"]
        assert REQ_S <= set(s) and s["статус"] in ("подходит", "почти", "нет")
        for r in s["расхождения"]:
            assert set(r) == {"характеристика", "требуется", "у_товара"}


def test_output_format_fresh():
    p = parse_notice_file(ROOT / "вход" / "eis" / "0813500000126020952.json")
    check_format(to_f(p, match_purchase(p, CAT)))


def test_output_format_all_demo_files():
    files = sorted(f for f in (ROOT / "демо_выход").glob("*.json") if f.stem[0].isdigit())
    assert len(files) >= 20
    for f in files:
        check_format(json.loads(f.read_text("utf-8")))


def test_cli_runs(tmp_path):
    env = dict(os.environ)
    env.pop("ANTHROPIC_API_KEY", None)
    r = subprocess.run([sys.executable, "-m", "tz_engine", str(ROOT / "вход" / "eis" / "0373200589126000121.json"),
                        "--каталог", str(ROOT / "каталог_демо.xlsx"), "--выход", str(tmp_path), "--тихо"],
                       cwd=ROOT, capture_output=True, text=True, env=env, timeout=120)
    assert r.returncode == 0, r.stderr
    out = json.loads((tmp_path / "0373200589126000121.json").read_text("utf-8"))
    check_format(out)
    assert (tmp_path / "сводка.csv").exists()


def test_cli_cyrillic_entry_point(tmp_path):
    r = subprocess.run([sys.executable, "-m", "движок.сверка", str(ROOT / "вход" / "eis" / "0373200589126000121.json"),
                        "--выход", str(tmp_path), "--тихо"], cwd=ROOT.parent, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "0373200589126000121.json").exists()


def test_own_price_list_columns(tmp_path):
    """Свой прайс с другими заголовками: столбцы распознаются по смыслу."""
    f = tmp_path / "прайс.csv"
    f.write_text("Артикул;Наименование;Категория;ОЗУ, Гб;Диагональ экрана, дюйм;Тип накопителя\n"
                 "A1;Ноутбук Тест 15;ноутбук;16;15,6;SSD\n", "utf-8")
    c = Catalog.load(f)
    assert len(c.products) == 1
    p = c.products[0]
    assert p["_category"] == "ноутбук" and p["ram"] == "16" and p["screen"] == "15,6" and p["storage_type"] == "SSD"
