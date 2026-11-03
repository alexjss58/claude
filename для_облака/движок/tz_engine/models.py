"""Структуры данных движка: закупка, позиция, требование, результат сверки."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Requirement:
    """Одна характеристика из техзадания с условием."""
    name: str
    op: str = "текст"            # >= | <= | = | диапазон | из_списка | текст
    value: str = ""              # как показать пользователю
    vmin: float | None = None
    vmax: float | None = None
    min_strict: bool = False     # «более» (>) вместо «не менее» (>=)
    max_strict: bool = False
    values: list[str] = field(default_factory=list)   # текстовые значения
    all_values: bool = False     # нужны все перечисленные значения (а не одно из)
    unit: str = ""
    equiv: bool = True           # «или эквивалент» допускается
    raw: str = ""                # исходный текст
    instruction: str = ""        # инструкция ЕИС по заполнению
    key: str | None = None       # канонический ключ (заполняет сопоставитель)

    def describe(self) -> str:
        from .units import pretty_unit
        u = f" {pretty_unit(self.unit)}" if self.unit and self.unit != "пиксель" else ""
        if self.values and self.op in (">=", "<=") and self.vmin is None and self.vmax is None:
            return f"{'≥' if self.op == '>=' else '≤'} {self.values[0]}"
        if self.op == ">=":
            return f"{'>' if self.min_strict else '≥'} {fmt(self.vmin)}{u}"
        if self.op == "<=":
            return f"{'<' if self.max_strict else '≤'} {fmt(self.vmax)}{u}"
        if self.op == "диапазон":
            return f"{fmt(self.vmin)}–{fmt(self.vmax)}{u}"
        if self.op == "=" and self.vmin is not None and not self.values:
            return f"= {fmt(self.vmin)}{u}"
        if self.values:
            sep = " + " if self.all_values else " / "
            return sep.join(self.values) + u
        return (self.value or self.raw) + u


def fmt(x: float | None) -> str:
    if x is None:
        return ""
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    return ("%.3f" % x).rstrip("0").rstrip(".").replace(".", ",")


@dataclass
class Position:
    num: int
    name: str
    ktru: str = ""
    okpd2: str = ""
    quantity: float | None = None
    unit: str = "шт"
    price: float | None = None
    requirements: list[Requirement] = field(default_factory=list)
    category: str | None = None
    brand_no_equiv: bool = False   # указан товарный знак без «или эквивалент»
    note: str = ""


@dataclass
class Purchase:
    number: str = ""
    subject: str = ""
    customer: str = ""
    customer_inn: str = ""
    law: str = "44-ФЗ"
    method: str = ""
    nmc: float | None = None
    region: str = ""
    deadline: str = ""
    url: str = ""
    source: str = ""
    foreign_restriction: bool | None = None
    positions: list[Position] = field(default_factory=list)
    parser: str = ""               # чем разобрали: eis-json / eis-xml / текст / llm


@dataclass
class Check:
    """Проверка одной характеристики у одного товара."""
    req: Requirement
    status: str          # ok | fail | unknown | unmapped
    have: str = ""


@dataclass
class MatchResult:
    status: str                   # подходит | почти | нет
    product: dict | None = None
    checks: list[Check] = field(default_factory=list)
    reason: str = ""

    @property
    def fails(self) -> list[Check]:
        return [c for c in self.checks if c.status == "fail"]

    @property
    def unknowns(self) -> list[Check]:
        return [c for c in self.checks if c.status in ("unknown", "unmapped")]


def to_dict(obj: Any) -> Any:
    return asdict(obj)
