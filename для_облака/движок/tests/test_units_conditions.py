"""Единицы и условия: «не менее 16 ГБ», «от 8 до 16», «IPS или VA», перевод единиц."""
import pytest

from tz_engine import units
from tz_engine.conditions import compare, parse_value, split_list, text_match


@pytest.mark.parametrize("text,op,vmin,vmax", [
    ("не менее 16 Гб", ">=", 16, None),
    ("≥ 2,5 ГГц", ">=", 2.5, None),
    ("16 ГБ и более", ">=", 16, None),
    ("более 4 ядер", ">=", 4, None),
    ("не более 2 кг", "<=", None, 2),
    ("менее 5 мс", "<=", None, 5),
    ("от 8 до 16 ГБ", "диапазон", 8, 16),
    ("≥8 и ≤16", "диапазон", 8, 16),
    ("в диапазоне от 0 до 40 °C", "диапазон", 0, 40),
    ("15,6 дюйма", "=", 15.6, 15.6),
    ("≥ -50", ">=", -50, None),
    ("до 64 ГБ", "<=", None, 64),
])
def test_numeric_conditions(text, op, vmin, vmax):
    r = parse_value(text, "x")
    assert r.op == op
    assert r.vmin == vmin
    assert r.vmax == vmax


def test_units_detected():
    assert units.lookup(parse_value("не менее 16 Гб").unit)[0] == "data"
    assert units.lookup(parse_value("≥ 2,5 ГГц").unit)[0] == "freq"
    assert units.lookup(parse_value("не менее 3000 ANSI лм").unit)[0] == "lm"
    assert units.lookup("Вт.ч")[0] == "energy"
    assert units.lookup("тыс. шт; 1000 шт") == ("count", 1000.0)


def test_unit_conversion():
    assert units.convert(1, "ТБ", "ГБ") == 1024
    assert units.convert(512, "Мбайт", "ГБ") == 0.5
    assert units.convert(1, "Гбит/с", "Мбит/с") == 1000
    assert units.convert(1, "кг", "ГГц") is None


def test_resolution_and_named_resolution():
    r = parse_value("не менее 1920 х 1080 пикселей")
    assert r.op == ">=" and r.values == ["1920x1080"]
    r2 = parse_value("Full HD", "Разрешение экрана")
    assert r2.values == ["1920x1080"]


def test_lists_and_equivalent():
    r = parse_value("IPS или VA")
    assert r.op == "из_списка" and r.values == ["IPS", "VA"]
    r = parse_value("HDMI, USB, RJ-45", "Наличие интерфейсов")
    assert r.all_values and r.values == ["HDMI", "USB", "RJ-45"]
    r = parse_value("Windows 11 Pro или эквивалент")
    assert r.equiv is True and r.values == ["Windows 11 Pro"]
    assert parse_value("Canon, эквивалент не допускается").equiv is False
    assert split_list("IPS (PLS, ADS)") == ["IPS (PLS, ADS)"]
    assert split_list("HDMI, Выход 3.5 (mini-Jack)") == ["HDMI", "Выход 3.5 (mini-Jack)"]


def test_yes_no_and_versions():
    assert parse_value("наличие").values == ["да"]
    assert parse_value("Нет").values == ["нет"]
    assert parse_value("2.0", "Версия HDMI").values == ["2.0"]


def test_compare_numbers_with_units():
    r = parse_value("не менее 16 Гб")
    assert compare(r, "16", "ГБ")[0] == "ok"
    assert compare(r, "8 ГБ")[0] == "fail"
    assert compare(r, "1 ТБ")[0] == "ok"
    r = parse_value("не менее 512 Мбайт")
    assert compare(r, "0.5", "ГБ")[0] == "ok"
    r = parse_value("от 220 до 240 В")
    assert compare(r, "162–290", "В")[0] == "ok"     # диапазон товара перекрывает требуемый


def test_compare_text_families():
    assert text_match("черно-белая (монохромная)", "Цветная") == "fail"
    assert text_match("лазерная (электрографическая)", "Электрографическая") == "ok"
    assert text_match("L3, управляемый", "Неуправляемый") == "fail"
    assert text_match("10/100/1000BASE-T (RJ-45)", "Медный") == "ok"
    assert text_match("накладные", "С двумя наушниками") == "unknown"   # в описании нет — не «нет», а «нет данных»
    assert text_match("HDMI 1.4; DisplayPort 1.4", "VGA", closed=True) == "fail"


def test_compare_kind_mismatch_is_unknown():
    r = parse_value("Дискретный", "Тип аудиоконтроллера")
    assert compare(r, "да", kind="bool")[0] == "unknown"
    r = parse_value("да", "Возможность работы в качестве DHCP-сервера")
    assert compare(r, "VLAN, QoS, LAG", kind="text", key="sw_features")[0] == "unknown"
    assert compare(r, "DHCP client/server", kind="text", key="sw_features")[0] == "ok"


def test_energy_class():
    r = parse_value("Не ниже A+", "Класс энергетической эффективности")
    assert compare(r, "A++", kind="text", key="energy_class")[0] == "ok"
    assert compare(r, "B", kind="text", key="energy_class")[0] == "fail"
