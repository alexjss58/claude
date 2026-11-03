"""Скачать реальные закупки 44-ФЗ / 223-ФЗ из открытого API ГосПлан и подготовить их для движка.

ГосПлан (https://gosplan.info) — открытое API к данным ЕИС. Тестовый сервер
https://v2test.gosplan.info работает без ключа и без регистрации, лимит 10 запросов
в минуту с одного IP. Мы ничего не регистрируем и никуда ничего не отправляем.

Что делает скрипт:
1. по номеру закупки берёт извещение (/fz44/purchases/{номер}/notification)
   и карточку закупки (/fz44/purchases/{номер}) — из неё ИНН заказчика и регион;
2. убирает из извещения ФИО, телефоны и почты контактных лиц (личные данные не храним);
3. кладёт файл в движок/вход/eis/<номер>.json.

Запуск:
    python инструменты/получить_закупки.py 0813500000126020952 0272100000426000191
    python инструменты/получить_закупки.py --из-кэша /путь/к/скачанным   # если файлы уже скачаны
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

BASE = "https://v2test.gosplan.info"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "вход" / "eis"
PERSONAL_KEYS = {"contactPersonInfo", "contactEMail", "contactPhone", "contactFax", "addInfo",
                 "contact", "contactPerson", "contactInfo", "additionalContactInfo"}


def fetch(path: str) -> bytes:
    for _ in range(15):
        try:
            req = urllib.request.Request(BASE + path, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(25)
                continue
            raise
        except OSError:
            time.sleep(10)
    raise RuntimeError("не удалось получить " + path)


def scrub(o):
    """Удалить контактные данные физических лиц."""
    if isinstance(o, dict):
        return {k: scrub(v) for k, v in o.items() if k not in PERSONAL_KEYS}
    if isinstance(o, list):
        return [scrub(x) for x in o]
    return o


def scrub_xml(path_in: Path, path_out: Path) -> None:
    tree = ET.parse(path_in)
    root = tree.getroot()
    for parent in root.iter():
        for ch in list(parent):
            if ch.tag.split("}", 1)[-1] in PERSONAL_KEYS:
                parent.remove(ch)
    tree.write(path_out, encoding="utf-8", xml_declaration=True)


def prepare(number: str, notice: dict | None, card: dict | None) -> dict:
    meta = {
        "purchase_number": number,
        "source": "структурированное извещение ЕИС (через открытое API ГосПлан, v2test.gosplan.info)",
        "retrieved": date.today().isoformat(),
        "api_url": f"{BASE}/{'fz223' if len(number) == 11 else 'fz44'}/purchases/{number}",
    }
    if card:
        meta["customer_inn"] = (card.get("customers") or [card.get("customer")] or [""])[0] or ""
        meta["region_code"] = card.get("region")
        meta["stage"] = card.get("stage")
        meta["purchase_type"] = card.get("purchase_type")
    out = {"_meta": meta}
    if notice:
        out["doc_type"] = notice.get("doc_type", "")
        out["source"] = scrub(notice.get("source", notice))
    elif card and card.get("docs"):
        # 223-ФЗ: извещение лежит прямо в карточке
        out["doc_type"] = card["docs"][0].get("doc_type", "")
        out["source223"] = scrub(card["docs"][0].get("source", {}))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("номера", nargs="*")
    ap.add_argument("--из-кэша", dest="cache", help="папка с файлами n_<номер>.json и p_<номер>.json")
    ap.add_argument("--xml", nargs="*", default=[], help="XML-извещения ЕИС: очистить и положить в вход/eis_xml")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    numbers = list(a.номера)
    if a.cache and not numbers:
        numbers = sorted({p.stem[2:] for p in Path(a.cache).glob("p_*.json")})
    for n in numbers:
        notice = card = None
        if a.cache:
            fn, fp = Path(a.cache) / f"n_{n}.json", Path(a.cache) / f"p_{n}.json"
            notice = json.loads(fn.read_text("utf-8")) if fn.exists() else None
            card = json.loads(fp.read_text("utf-8")) if fp.exists() else None
        else:
            law = "fz223" if len(n) == 11 else "fz44"
            if law == "fz44":
                notice = json.loads(fetch(f"/fz44/purchases/{n}/notification"))
                time.sleep(7)
            card = json.loads(fetch(f"/{law}/purchases/{n}"))
            time.sleep(7)
        data = prepare(n, notice, card)
        (OUT / f"{n}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), "utf-8")
        print("готово:", n)
    if a.xml:
        xo = ROOT / "вход" / "eis_xml"
        xo.mkdir(parents=True, exist_ok=True)
        for x in a.xml:
            scrub_xml(Path(x), xo / Path(x).name)
            print("xml:", Path(x).name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
