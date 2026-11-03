#!/usr/bin/env python3
"""Обновление выгрузки Евразийского реестра промышленных товаров (ЕЭК) для проверки нацрежима.

Что делает: берёт открытый REST API ЕЭК (без входа и регистрации), отбирает позиции
по ОКПД2 26.20, 26.30, 26.40, 26.51 и по группам ТН ВЭД ЕАЭС (компьютеры, связь, аудио-видео,
приборы), пишет csv и xlsx, добавляет строку в журнал обновлений.
Если источник недоступен или ответ не такой, как ждали, скрипт падает с понятным сообщением
(код выхода 2) и старые файлы НЕ затирает.

Запуск:  python3 обновить.py            (нужны пакеты requests и openpyxl)
Не юридическая консультация.
"""
import csv, json, re, sys, time
from datetime import datetime
from pathlib import Path
import requests
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

ПАПКА = Path(__file__).resolve().parent
API = "https://goszakupki.eaeunion.org/spd/find"
КОЛЛЕКЦИЯ = "erpt.v_goodscollection_prod_public"
ИСТОЧНИК = "https://goszakupki.eaeunion.org/erpt/ru/registers/products/"
СПЕЦ = "https://goszakupki.eaeunion.org/erpt/assets/files/"  # PDF со спецификацией API
ПАЧКА = 1000  # максимум по спецификации API
# ОКПД2: компьютеры 26.20, связь 26.30, аудио-видео 26.40, приборы 26.51
ОКПД2_RE = r"^26\.(20|30|40|51)"
# ТН ВЭД в реестре записан с пробелами, например "8471 41 000 0"
ТНВЭД_RE = r"^(8471|8517|8518|8519|8521|8525|9015|9024|9025|9026|9027|9028|9029|9030|9031)"
СТРАНЫ = {"01": "Армения", "02": "Беларусь", "03": "Казахстан", "04": "Киргизия", "05": "Россия"}
СТАТУС = {2: "Действует", 5: "Аннулирована", 7: "Истёк срок документа"}
ТИП_ДОК = {"1": "Акт экспертизы", "2": "Сертификат СТ-1"}
КОЛОНКИ = ["производитель", "страна", "ИНН/идент. код производителя", "наименование товара", "ОКПД2", "ТН ВЭД",
           "реестровый номер", "дата внесения", "срок действия до", "статус", "баллы", "тип документа",
           "документ о происхождении", "адрес производителя", "причина отбора", "источник"]


def падаем(текст):
    print("ОШИБКА: " + текст, file=sys.stderr)
    sys.exit(2)


def запрос(фильтр, skip, limit=ПАЧКА):
    параметры = {"collection": КОЛЛЕКЦИЯ, "limit": limit, "skip": skip, "sort": json.dumps({"_id": 1})}
    for попытка in range(3):
        try:
            r = requests.post(API, params=параметры, data=json.dumps(фильтр),
                              headers={"Content-Type": "text/plain"}, timeout=90)
            if r.status_code != 200:
                raise RuntimeError(f"HTTP {r.status_code}")
            данные = r.json()
            if "result" not in данные or "matchedDocuments" not in данные:
                падаем("API ответил, но формат другой (нет result/matchedDocuments). Возможно, ЕЭК изменила API. "
                       f"Спецификация: {СПЕЦ}")
            return данные
        except (requests.RequestException, RuntimeError, ValueError) as e:
            err = e
            time.sleep(3 * (попытка + 1))
    падаем(f"источник недоступен: {API} ({err}). Файлы в папке не изменены. Проверьте сеть и откройте {ИСТОЧНИК}")


def строка(r):
    окпд, тн = r.get("goodsokpd2", "") or "", r.get("tnved", "") or ""
    причины = []
    if re.match(ОКПД2_RE, окпд): причины.append("ОКПД2")
    if re.match(ТНВЭД_RE, тн): причины.append("ТН ВЭД")
    return [r.get("name", "").strip(), СТРАНЫ.get(r.get("statemember"), r.get("statemember", "")), r.get("identitycode", ""),
            (r.get("goodsname") or "").replace("\t", " ").strip(), окпд, тн, r.get("registrynumber", ""),
            (r.get("publishdate") or "")[:10], r.get("expertactenddate", ""),
            СТАТУС.get(r.get("applicationitemstatus"), str(r.get("applicationitemstatus", ""))), r.get("points"),
            ТИП_ДОК.get(r.get("documentype"), r.get("documentype", "")), (r.get("documentname") or "").strip(),
            (r.get("address") or "").strip(), "+".join(причины) or "?", ИСТОЧНИК]
    # поле "user" (ФИО сотрудника ЕЭК) в выгрузку не берём: личные данные не нужны


def main():
    начало = datetime.now()
    фильтр = {"$or": [{"goodsokpd2": {"$regex": ОКПД2_RE}}, {"tnved": {"$regex": ТНВЭД_RE}}]}
    первая = запрос(фильтр, 0)
    всего, в_реестре = первая["matchedDocuments"], первая.get("totalDocuments")
    if всего == 0:
        падаем("по фильтру найдено 0 записей: так не бывает, вероятно API изменился. Файлы не изменены.")
    строки, skip, ответ = [], 0, первая
    while True:
        строки += [строка(r) for r in ответ["result"]]
        skip += ПАЧКА
        if skip >= всего: break
        ответ = запрос(фильтр, skip)
    if len(строки) != всего:
        падаем(f"получено {len(строки)} строк, а API обещал {всего}. Файлы не изменены.")
    строки.sort(key=lambda x: (x[0].lower(), x[3].lower(), x[6]))
    # запись только после полного успеха
    with open(ПАПКА / "реестр_ЕАЭС_26xx.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";"); w.writerow(КОЛОНКИ); w.writerows(строки)
    wb = Workbook(); ws = wb.active; ws.title = "Евразийский реестр"
    ws.append(КОЛОНКИ)
    for c in ws[1]: c.font = Font(bold=True)
    for s in строки: ws.append(s)
    ws.freeze_panes = "A2"; ws.auto_filter.ref = ws.dimensions
    for i, ширина in enumerate([40, 11, 16, 60, 14, 16, 14, 12, 14, 18, 8, 16, 40, 40, 14, 50], 1):
        ws.column_dimensions[get_column_letter(i)].width = ширина
    ws2 = wb.create_sheet("О выгрузке")
    действует = sum(1 for s in строки if s[9] == "Действует")
    for a in [["Источник", ИСТОЧНИК], ["API", f"{API}?collection={КОЛЛЕКЦИЯ}"], ["Спецификация API", СПЕЦ],
              ["Дата выгрузки", начало.strftime("%Y-%m-%d %H:%M")], ["Записей в выгрузке", len(строки)],
              ["из них со статусом «Действует»", действует], ["Всего записей в реестре ЕЭК", в_реестре],
              ["Отбор", f"ОКПД2 по маске {ОКПД2_RE} или ТН ВЭД по маске {ТНВЭД_RE}"],
              ["Важно", "Это ЕВРАЗИЙСКИЙ реестр (ЕЭК), а не реестр ГИСП (ПП 719). Не юридическая консультация."]]:
        ws2.append(a)
    ws2.column_dimensions["A"].width = 32; ws2.column_dimensions["B"].width = 100
    wb.save(ПАПКА / "реестр_ЕАЭС_26xx.xlsx")
    с_россии = sum(1 for s in строки if s[1] == "Россия")
    with open(ПАПКА / "журнал_обновлений.log", "a", encoding="utf-8") as f:
        f.write(f"{начало:%Y-%m-%d %H:%M} OK записей={len(строки)} действует={действует} россия={с_россии} в_реестре_всего={в_реестре}\n")
    print(f"Готово: {len(строки)} записей (действует: {действует}, Россия: {с_россии}); всего в реестре ЕЭК: {в_реестре}")


if __name__ == "__main__":
    main()
