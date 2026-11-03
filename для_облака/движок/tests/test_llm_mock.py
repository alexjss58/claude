"""Режим Claude API без сети: подменяем пакет anthropic и проверяем, что ответ модели превращается в позиции."""
import json
import sys
import types

from tz_engine import llm


class _Usage:
    input_tokens = 5000
    output_tokens = 1500


class _Block:
    type = "text"

    def __init__(self, text):
        self.text = text


class _Resp:
    stop_reason = "end_turn"
    model = "claude-sonnet-5-5"
    usage = _Usage()

    def __init__(self, data):
        self.content = [_Block(json.dumps(data, ensure_ascii=False))]


ANSWER = {"номер": "0813500000126020952", "предмет": "Поставка ноутбуков", "заказчик": "МБУ",
          "позиции": [{"наименование": "Ноутбук", "ктру": "26.20.11.110-00000139", "окпд2": "26.20.11.110",
                       "количество": 14, "единица": "шт",
                       "характеристики": [
                           {"имя": "Диагональ экрана", "условие": ">=", "мин": 16, "макс": None, "строго": False,
                            "значения": [], "все_значения": False, "единица": "дюйм", "эквивалент_допускается": True},
                           {"имя": "Тип накопителя", "условие": "=", "мин": None, "макс": None, "строго": False,
                            "значения": ["SSD"], "все_значения": False, "единица": "", "эквивалент_допускается": True}]}]}


def test_llm_parse_with_fake_sdk(monkeypatch):
    calls = {}

    class _Beta:
        class messages:  # noqa: N801
            @staticmethod
            def create(**kw):
                calls.update(kw)
                return _Resp(ANSWER)

    class _Client:
        beta = _Beta()

    fake = types.ModuleType("anthropic")
    fake.Anthropic = lambda: _Client()
    monkeypatch.setitem(sys.modules, "anthropic", fake)
    pur, info = llm.parse_text("Ноутбук. Диагональ не менее 16 дюймов. Накопитель SSD.")
    assert calls["model"] == "claude-sonnet-5-5"
    assert calls["output_config"]["format"]["type"] == "json_schema"
    assert pur.positions[0].requirements[0].op == ">=" and pur.positions[0].requirements[0].vmin == 16
    assert pur.positions[0].requirements[1].values == ["SSD"]
    assert info["долл"] > 0


def test_llm_disabled_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert llm.available() is False


def test_cost_estimate_reasonable():
    est = llm.estimate_cost("а" * 27000)
    assert 10000 < est["токенов_вход"] < 20000 and est["долл"] < 1
