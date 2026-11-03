"""Оценка против эталона запускается и даёт осмысленные числа."""
from tz_engine import evaluate


def test_evaluate_runs():
    rep = evaluate.run()
    s = rep["разбор"]["ЕИС-json"]
    assert s["хар_эталон"] >= 100
    assert s["полностью_верно"] / s["хар_эталон"] > 0.9
    m = rep["сверка"]["ЕИС-json"]
    assert m["позиций"] == 7
