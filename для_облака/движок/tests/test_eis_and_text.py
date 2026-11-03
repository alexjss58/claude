"""Разбор реальных извещений ЕИС и документов (docx/pdf/xlsx/txt)."""
from pathlib import Path

import pytest

from tz_engine.eis import parse_notice_file
from tz_engine.readers import read_document
from tz_engine.text_parser import parse_doc

ROOT = Path(__file__).resolve().parents[1]
EIS = ROOT / "вход" / "eis"
DOCS = ROOT / "вход" / "документы_реконструкция"


def test_notice_laptops():
    p = parse_notice_file(EIS / "0813500000126020952.json")
    assert p.number == "0813500000126020952"
    assert p.law == "44-ФЗ" and p.nmc == 936600.0
    assert len(p.positions) == 1
    pos = p.positions[0]
    assert pos.ktru == "26.20.11.110-00000139" and pos.quantity == 14
    reqs = {r.name: r for r in pos.requirements}
    assert len(reqs) == 23
    assert reqs["Диагональ экрана"].op == ">=" and reqs["Диагональ экрана"].vmin == 16
    assert reqs["Вес"].op == "<=" and reqs["Вес"].vmax == 2.1
    assert reqs["Наличие сенсорного экрана"].values == ["нет"]


def test_notice_multi_value_all_required():
    p = parse_notice_file(EIS / "0340100010926000063.json")
    reqs = {r.name: r for r in p.positions[0].requirements}
    r = reqs["Тип монтажа"]
    assert r.all_values and r.values == ["Настольный", "Потолочный"]
    assert reqs["Контрастность"].op == ">=" and reqs["Контрастность"].vmin == 20000   # «≥ 20 000:1» текстом


def test_notice_223_has_positions_without_characteristics():
    p = parse_notice_file(EIS / "32616496528.json")
    assert p.law == "223-ФЗ" and len(p.positions) == 5
    assert all(not x.requirements for x in p.positions)


def test_notice_xml():
    p = parse_notice_file(ROOT / "вход" / "eis_xml" / "0372200119426000012.xml")
    assert p.number == "0372200119426000012" and p.positions and p.positions[0].requirements


def test_personal_data_removed():
    for f in EIS.glob("*.json"):
        t = f.read_text("utf-8")
        assert "contactPersonInfo" not in t and "contactEMail" not in t and "contactPhone" not in t


@pytest.mark.parametrize("name", ["0820500000826005372_таблица.docx", "0820500000826005372_таблица.pdf",
                                  "0820500000826005372_таблица.xlsx", "0820500000826005372_текст.txt",
                                  "0820500000826005372_текст.docx"])
def test_documents_all_formats(name):
    ref = parse_notice_file(EIS / "0820500000826005372.json")
    got = parse_doc(read_document(DOCS / name))
    assert got.number == "0820500000826005372"
    assert len(got.positions) == 1
    assert got.positions[0].ktru == ref.positions[0].ktru
    assert got.positions[0].quantity == 70
    names_ref = {r.name for r in ref.positions[0].requirements}
    names_got = {r.name for r in got.positions[0].requirements}
    assert len(names_ref & names_got) >= len(names_ref) - 1


def test_free_text_small(tmp_path):
    f = tmp_path / "тз.txt"
    f.write_text("Техническое задание\nОбъект закупки: Поставка ноутбуков\n"
                 "1. Ноутбук — 5 шт. (КТРУ 26.20.11.110-00000139)\n"
                 "Диагональ экрана: не менее 15,6 дюйма\n"
                 "Оперативная память не менее 16 ГБ\n"
                 "Тип матрицы: IPS или эквивалент\n"
                 "Срок поставки: 30 дней\n", "utf-8")
    p = parse_doc(read_document(f))
    assert len(p.positions) == 1
    pos = p.positions[0]
    assert pos.quantity == 5 and pos.ktru == "26.20.11.110-00000139"
    names = [r.name for r in pos.requirements]
    assert names == ["Диагональ экрана", "Оперативная память", "Тип матрицы"]
    assert pos.requirements[1].op == ">=" and pos.requirements[1].vmin == 16


def test_unsupported_doc_format(tmp_path):
    f = tmp_path / "старый.doc"
    f.write_bytes(b"x")
    with pytest.raises(ValueError):
        read_document(f)


def test_messy_docx_layout(tmp_path):
    """Заголовок позиции абзацем + отдельная таблица характеристик; объединённые ячейки; «или эквивалент»."""
    import docx
    d = docx.Document()
    d.add_paragraph("Описание объекта закупки")
    d.add_paragraph("Товар № 1: Монитор (КТРУ 26.20.17.110-00000007), количество: 10 шт.")
    t = d.add_table(rows=4, cols=3)
    for j, h in enumerate(["Наименование характеристики", "Значение характеристики", "Единица измерения характеристики"]):
        t.rows[0].cells[j].text = h
    rows = [("Размер диагонали", "не менее 23,8", "дюйм"), ("Тип матрицы", "IPS или эквивалент", ""),
            ("Яркость", "от 250 до 350", "кд/м2")]
    for i, (a, b, c) in enumerate(rows, 1):
        t.rows[i].cells[0].text, t.rows[i].cells[1].text, t.rows[i].cells[2].text = a, b, c
    d.add_paragraph("Товар № 2: Принтер — 2 шт.")
    t2 = d.add_table(rows=3, cols=2)
    t2.rows[0].cells[0].text, t2.rows[0].cells[1].text = "Характеристика", "Требуемое значение"
    t2.rows[1].cells[0].text, t2.rows[1].cells[1].text = "Скорость печати", "не менее 30 стр/мин"
    t2.rows[2].cells[0].text, t2.rows[2].cells[1].text = "Цветность", "черно-белая"
    t2.cell(2, 0).merge(t2.cell(2, 0))
    f = tmp_path / "грязный.docx"
    d.save(str(f))
    p = parse_doc(read_document(f))
    assert [x.name for x in p.positions] == ["Монитор", "Принтер"]
    mon, pr = p.positions
    assert mon.ktru == "26.20.17.110-00000007"
    r = {x.name: x for x in mon.requirements}
    assert r["Размер диагонали"].op == ">=" and r["Размер диагонали"].vmin == 23.8 and r["Размер диагонали"].unit
    assert r["Тип матрицы"].equiv is True and r["Тип матрицы"].values == ["IPS"]
    assert r["Яркость"].op == "диапазон" and (r["Яркость"].vmin, r["Яркость"].vmax) == (250, 350)
    assert pr.quantity == 2 and {x.name for x in pr.requirements} == {"Скорость печати", "Цветность"}
