"""Режим «живой»: разбор текста техзадания через Claude API.

Включается, только если задана переменная окружения ANTHROPIC_API_KEY (ключ в код не кладём).
Модель по умолчанию — claude-sonnet-5-5, её можно поменять переменной TZ_ENGINE_MODEL.
Нужен пакет anthropic:  pip install anthropic

Claude получает текст документа целиком и возвращает строго JSON по схеме ниже
(структурированный вывод, output_config.format). Дальше работает та же сверка, что и в режиме правил.
Для 44-ФЗ с извещением ЕИС модель не нужна: характеристики уже структурированы.
"""
from __future__ import annotations

import json
import os
import time

from .models import Position, Purchase, Requirement, fmt

DEFAULT_MODEL = "claude-sonnet-5-5"

# цены за 1 млн токенов, долл. США (справочник Claude API, кэш от 06.10.2026) — ОЦЕНКА, сверять с прайсом
PRICES = {"claude-sonnet-5-5": (2.00, 10.00), "claude-haiku-5-5": (0.10, 0.50), "claude-opus-5-5": (4.00, 20.00)}

SCHEMA = {
    "type": "object",
    "properties": {
        "номер": {"type": "string"},
        "предмет": {"type": "string"},
        "заказчик": {"type": "string"},
        "позиции": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "наименование": {"type": "string"},
                    "ктру": {"type": "string"},
                    "окпд2": {"type": "string"},
                    "количество": {"type": "number"},
                    "единица": {"type": "string"},
                    "характеристики": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "имя": {"type": "string"},
                                "условие": {"type": "string", "enum": [">=", "<=", "=", "диапазон", "из_списка", "текст"]},
                                "мин": {"type": ["number", "null"]},
                                "макс": {"type": ["number", "null"]},
                                "строго": {"type": "boolean"},
                                "значения": {"type": "array", "items": {"type": "string"}},
                                "все_значения": {"type": "boolean"},
                                "единица": {"type": "string"},
                                "эквивалент_допускается": {"type": "boolean"},
                            },
                            "required": ["имя", "условие", "мин", "макс", "строго", "значения", "все_значения", "единица",
                                         "эквивалент_допускается"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["наименование", "ктру", "окпд2", "количество", "единица", "характеристики"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["номер", "предмет", "заказчик", "позиции"],
    "additionalProperties": False,
}

SYSTEM = (
    "Ты разбираешь «Описание объекта закупки» (техническое задание) российской госзакупки по 44-ФЗ или 223-ФЗ. "
    "Выпиши каждую поставляемую позицию товара и все её характеристики. Для каждой характеристики укажи условие: "
    "«>=» для «не менее/не ниже/≥», «<=» для «не более/не выше/≤», «диапазон» для «от … до …», «=» для точного значения "
    "или одного текстового значения, «из_списка» если допускается одно из перечисленных значений, «текст» для описаний. "
    "Числа пиши в поля мин/макс (строго=true для «более»/«менее» без «не»), текстовые значения — в «значения». "
    "все_значения=true, если товар должен иметь все перечисленные значения. Единицу пиши как в документе. "
    "эквивалент_допускается=false только если в тексте прямо сказано, что эквивалент не допускается, или указан товарный знак без слов «или эквивалент». "
    "Не придумывай ничего, чего нет в тексте; требования к срокам, оплате, упаковке и гарантии не являются характеристиками товара."
)


def available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def estimate_tokens(text: str) -> int:
    """Грубая оценка числа токенов для русского текста (≈ 2,7 символа на токен). Это ОЦЕНКА."""
    return int(len(text) / 2.7) + 400


def estimate_cost(text: str, model: str | None = None, out_ratio: float = 0.6) -> dict:
    model = model or os.environ.get("TZ_ENGINE_MODEL", DEFAULT_MODEL)
    pin, pout = PRICES.get(model, PRICES[DEFAULT_MODEL])
    tin = estimate_tokens(text) + estimate_tokens(SYSTEM) + 1500   # + схема
    tout = int(estimate_tokens(text) * out_ratio)
    usd = tin / 1e6 * pin + tout / 1e6 * pout
    return {"модель": model, "токенов_вход": tin, "токенов_выход": tout, "долл": round(usd, 4)}


def _to_purchase(data: dict) -> Purchase:
    pur = Purchase(number=data.get("номер", ""), subject=data.get("предмет", ""), customer=data.get("заказчик", ""),
                   parser="Claude API")
    for i, p in enumerate(data.get("позиции", []), 1):
        pos = Position(num=i, name=p.get("наименование", ""), ktru=p.get("ктру", ""), okpd2=p.get("окпд2", ""),
                       quantity=p.get("количество"), unit=p.get("единица") or "шт")
        for c in p.get("характеристики", []):
            r = Requirement(name=c["имя"], op=c["условие"], vmin=c.get("мин"), vmax=c.get("макс"),
                            values=list(c.get("значения") or []), all_values=bool(c.get("все_значения")),
                            unit=c.get("единица") or "", equiv=bool(c.get("эквивалент_допускается", True)))
            if r.op == ">=":
                r.min_strict = bool(c.get("строго"))
            if r.op == "<=":
                r.max_strict = bool(c.get("строго"))
            if r.op == "=" and r.values == [] and r.vmin is None and r.vmax is not None:
                r.vmin = r.vmax
            r.value = (fmt(r.vmin) if r.vmin is not None else "") or "; ".join(r.values)
            r.raw = r.describe()
            pos.requirements.append(r)
        pur.positions.append(pos)
    return pur


def parse_text(text: str, model: str | None = None) -> tuple[Purchase, dict]:
    """Разобрать текст ТЗ через Claude. Возвращает (закупка, сведения о вызове: токены, время, стоимость)."""
    import anthropic  # импорт здесь: без ключа и пакета движок работает в режиме правил

    model = model or os.environ.get("TZ_ENGINE_MODEL", DEFAULT_MODEL)
    client = anthropic.Anthropic()
    kwargs = dict(
        model=model,
        max_tokens=32000,
        system=SYSTEM,
        messages=[{"role": "user", "content": "Текст документа:\n\n" + text}],
        output_config={"format": {"type": "json_schema", "schema": SCHEMA}, "effort": "low"},
    )
    t0 = time.perf_counter()
    if model.startswith("claude-haiku"):
        resp = client.messages.create(**kwargs)
    else:
        # при отказе фильтра запрос автоматически повторяется на рекомендованной модели
        resp = client.beta.messages.create(betas=["server-side-fallback-2026-07-01"], fallbacks="default", **kwargs)
    dt = time.perf_counter() - t0
    if resp.stop_reason == "refusal":
        raise RuntimeError("модель отказалась обрабатывать документ (stop_reason=refusal)")
    if resp.stop_reason == "max_tokens":
        raise RuntimeError("ответ модели обрезан по max_tokens — документ слишком большой, разбейте его на части")
    txt = next(b.text for b in resp.content if b.type == "text")
    data = json.loads(txt)
    pin, pout = PRICES.get(model, PRICES[DEFAULT_MODEL])
    u = resp.usage
    info = {"модель": resp.model, "секунд": round(dt, 1), "токенов_вход": u.input_tokens, "токенов_выход": u.output_tokens,
            "долл": round(u.input_tokens / 1e6 * pin + u.output_tokens / 1e6 * pout, 4)}
    return _to_purchase(data), info
