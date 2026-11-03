// Демо-режим слоя ИИ: разбор техзадания и сверка с ассортиментом по простым правилам,
// без ключей и без сети. Результат — в формате движка блока G («G → F»).
// Это не настоящий движок: он понимает только аккуратные строки вида
// «Объём оперативной памяти: не менее 16 ГБ». Настоящий разбор — блок G или «живой» режим.

import type { CatalogItem, Позиция, Расхождение, Sverka, Характеристика } from '../types';
import { categoryFromName } from '../lib/catalog';

// Синонимы названий характеристик: требование в техзадании → ключ в прайсе
const KEY_SYNONYMS: [RegExp, RegExp][] = [
  [/оперативн|озу|ram/i, /озу|оперативн|ram/i],
  [/ssd|накопител|диск/i, /ssd|накопител|диск/i],
  [/диагональ/i, /диагональ/i],
  [/разрешение/i, /разрешение/i],
  [/матриц/i, /матриц/i],
  [/процессор/i, /процессор/i],
  [/масса|вес/i, /вес|масса/i],
  [/скорость печати/i, /скорость печати/i],
  [/двусторон/i, /двусторон/i],
  [/ethernet|сетев\w* интерфейс/i, /ethernet/i],
  [/автоподатчик/i, /автоподатчик/i],
  [/формат/i, /формат/i],
  [/полная мощность|мощность.*ва/i, /^мощность$/i],
  [/активная мощность|выходн\w* мощность/i, /выходная мощность/i],
  [/форма\w* (выходного )?сигнал/i, /форма сигнала/i],
  [/розет/i, /розет/i],
  [/sip/i, /sip/i],
  [/poe/i, /poe/i],
  [/порт\w* (ethernet )?1 ?гбит|порт/i, /портов 1 гбит/i],
  [/яркост/i, /яркост/i],
  [/канал/i, /канал/i],
  [/usb-?аудио|usb-интерфейс/i, /usb-аудио/i],
  [/трубок|трубк/i, /трубок/i],
  [/определител|аон/i, /аон/i],
  [/шумоподав/i, /шумоподав/i],
  [/подключени/i, /подключени/i],
  [/дальност/i, /дальност/i],
  [/диапазон частот|диапазон$/i, /диапазон/i],
  [/технолог/i, /технолог/i],
  [/hdmi/i, /hdmi|интерфейс/i],
  [/интерфейс/i, /интерфейс/i],
  [/регулировк/i, /регулировк/i],
  [/нч-динамик|динамик/i, /нч-динамик/i],
  [/пиков\w* мощност/i, /мощность пиковая/i],
  [/^тип$/i, /^тип$/i],
];

function toNum(s: string): number | null {
  const m = /(-?\d+(?:[.,]\d+)?)/.exec(s.replace(/\s/g, ''));
  return m ? Number(m[1].replace(',', '.')) : null;
}

function resolution(s: string): number | null {
  const m = /(\d{3,4})\s*[x×х*]\s*(\d{3,4})/i.exec(s);
  return m ? Number(m[1]) * Number(m[2]) : null;
}

function specFor(item: CatalogItem, reqName: string): [string, string] | null {
  const pair = KEY_SYNONYMS.find(([r]) => r.test(reqName));
  const entries = Object.entries(item.характеристики);
  if (pair) {
    const hit = entries.find(([k]) => pair[1].test(k));
    if (hit) return hit;
  }
  const direct = entries.find(([k]) => k.toLowerCase() === reqName.toLowerCase());
  return direct || null;
}

/** Значение характеристики товара для требования (для таблицы в черновике заявки) */
export function specValue(item: CatalogItem, reqName: string): string | null {
  const s = specFor(item, reqName);
  return s ? s[1] : null;
}

type Check = { ok: boolean | null; have: string };

function check(c: Характеристика, have: string): Check {
  const cond = c.условие;
  if (cond === '>=' || cond === '<=') {
    const r = resolution(c.значение), h = resolution(have);
    const need = r ?? toNum(c.значение), got = r !== null ? h : toNum(have);
    if (need === null || got === null) return { ok: null, have };
    return { ok: cond === '>=' ? got >= need : got <= need, have };
  }
  if (cond === 'диапазон') {
    const m = /(\d+(?:[.,]\d+)?)\s*[–-]\s*(\d+(?:[.,]\d+)?)/.exec(c.значение);
    const got = toNum(have);
    if (!m || got === null) return { ok: null, have };
    return { ok: got >= Number(m[1].replace(',', '.')) && got <= Number(m[2].replace(',', '.')), have };
  }
  if (cond === 'из_списка') {
    const opts = c.значение.split(/[;,/]| или /).map((x) => x.trim().toLowerCase()).filter(Boolean);
    const h = have.toLowerCase();
    return { ok: opts.some((o) => h.includes(o) || o.includes(h)), have };
  }
  if (cond === '=') {
    const r = resolution(c.значение), h = resolution(have);
    if (r !== null && h !== null) return { ok: h === r, have };
    const a = c.значение.toLowerCase().trim(), b = have.toLowerCase().trim();
    if (!a) return { ok: null, have };
    return { ok: b.includes(a) || a.includes(b) || (a === 'да' && /^да/.test(b)), have };
  }
  return { ok: null, have };
}

function describe(c: Характеристика): string {
  const u = c.единица ? ` ${c.единица}` : '';
  switch (c.условие) {
    case '>=': return `не менее ${c.значение}${u}`;
    case '<=': return `не более ${c.значение}${u}`;
    case 'диапазон': return `${c.значение}${u}`;
    case 'из_списка': return `одно из: ${c.значение}`;
    default: return `${c.значение}${u}`;
  }
}

/** Сверка одной позиции с ассортиментом: берём лучший товар нужной категории */
export function matchPosition(p: Omit<Позиция, 'сверка'>, catalog: CatalogItem[]): Позиция['сверка'] {
  const cat = categoryFromName(p.наименование);
  const candidates = catalog.filter((it) => cat !== 'Прочее' && (it.категория === cat || categoryFromName(it.наименование) === cat));
  if (!candidates.length) {
    return { статус: 'нет', товар_из_каталога: '', артикул: '', расхождения: [{ характеристика: 'Категория товара', требуется: p.наименование.toLowerCase(), у_товара: 'нет в ассортименте' }] };
  }
  let best: { item: CatalogItem; bad: Расхождение[]; checked: number } | null = null;
  for (const item of candidates) {
    const bad: Расхождение[] = [];
    let checked = 0;
    for (const c of p.характеристики) {
      const spec = specFor(item, c.имя);
      if (!spec) continue;
      const r = check(c, spec[1]);
      if (r.ok === null) continue;
      checked++;
      if (!r.ok) bad.push({ характеристика: c.имя, требуется: describe(c), у_товара: r.have });
    }
    if (!best || bad.length < best.bad.length || (bad.length === best.bad.length && checked > best.checked)) best = { item, bad, checked };
  }
  const b = best!;
  if (b.checked === 0 && p.характеристики.length > 0) {
    // Ни одну характеристику не удалось сравнить автоматически — честно говорим «почти, проверить вручную».
    return { статус: 'почти', товар_из_каталога: b.item.наименование, артикул: b.item.артикул,
      расхождения: [{ характеристика: 'Характеристики', требуется: 'по техзаданию', у_товара: 'не удалось сверить автоматически — проверить вручную' }] };
  }
  const status = b.bad.length === 0 ? 'подходит' : b.bad.length <= 2 ? 'почти' : 'нет';
  return { статус: status, товар_из_каталога: b.item.наименование, артикул: b.item.артикул, расхождения: b.bad };
}

/** Пересчитать готовую сверку (позиции из техзадания) по другому ассортименту */
export function recheck(s: Sverka, catalog: CatalogItem[]): Sverka {
  const позиции = s.позиции.map((p) => ({ ...p, сверка: matchPosition(p, catalog) }));
  return { ...s, позиции, итог: tally(позиции), режим: 'демо' };
}

export function tally(pos: Позиция[]) {
  const t = { подходит: 0, почти: 0, нет: 0 };
  for (const p of pos) t[p.сверка.статус]++;
  return t;
}

// ---- Разбор вставленного текста техзадания ----

const POS_RE = /^\s*(?:позиция\s*)?(\d{1,3})[.)]\s*(.+)$/i;
const QTY_RE = /(?:—|-|,|\(|\s)\s*(\d+(?:[.,]\d+)?)\s*(шт|штук|компл|комплект\w*|ед|упак)\.?/i;

export function parseCondition(raw: string): Omit<Характеристика, 'имя'> {
  const s = raw.trim();
  const equiv = !/эквивалент не допуск|без эквивалент/i.test(s);
  const clean = s.replace(/\(?или эквивалент\)?|эквивалент не допускается/gi, '').trim();
  let m = /^(?:не менее|не ниже|от|≥|>=|минимум)\s*(.+)$/i.exec(clean);
  if (m && !/\sдо\s/i.test(clean)) return withUnit('>=', m[1], equiv);
  m = /^(?:не более|не выше|до|≤|<=|максимум)\s*(.+)$/i.exec(clean);
  if (m) return withUnit('<=', m[1], equiv);
  m = /^(?:от\s*)?(\d+(?:[.,]\d+)?)\s*(?:до|–|-)\s*(\d+(?:[.,]\d+)?)\s*(.*)$/i.exec(clean);
  if (m) return { условие: 'диапазон', значение: `${m[1]}–${m[2]}`, единица: m[3].trim(), эквивалент_допускается: equiv };
  if (/;|\sили\s/.test(clean) && !/^\d/.test(clean)) return { условие: 'из_списка', значение: clean.replace(/\sили\s/g, '; '), единица: '', эквивалент_допускается: equiv };
  return withUnit('=', clean, equiv);
}

function withUnit(cond: string, v: string, equiv: boolean): Omit<Характеристика, 'имя'> {
  const m = /^(\d+(?:[.,]\d+)?(?:\s*[x×х]\s*\d+)?)\s*(.*)$/i.exec(v.trim());
  if (m) return { условие: cond, значение: m[1].replace(',', '.').replace(/\s/g, ''), единица: m[2].replace(/[.;]$/, '').trim(), эквивалент_допускается: equiv };
  return { условие: cond === '=' ? '=' : 'текст', значение: v.trim(), единица: '', эквивалент_допускается: equiv };
}

export function parseTzText(text: string): Omit<Позиция, 'сверка'>[] {
  const out: Omit<Позиция, 'сверка'>[] = [];
  let cur: Omit<Позиция, 'сверка'> | null = null;
  for (const line of text.split(/\r?\n/)) {
    const l = line.trim();
    if (!l) continue;
    const pm = POS_RE.exec(l);
    if (pm && !/[:]/.test(pm[2].split(/—|-/)[0])) {
      const q = QTY_RE.exec(pm[2]);
      const name = pm[2].replace(QTY_RE, '').replace(/[—–-]\s*$/, '').trim();
      cur = { '№': Number(pm[1]), наименование: name, ктру: '', окпд2: '', количество: q ? Number(q[1].replace(',', '.')) : 1, единица: q ? q[2].replace(/штук/i, 'шт') : 'шт', характеристики: [] };
      const ok = /(\d{2}\.\d{2}\.\d{2}\.\d{3})/.exec(l);
      if (ok) cur.окпд2 = ok[1];
      out.push(cur);
      continue;
    }
    const cm = /^[•·\-–—*]?\s*([^:]{2,80}):\s*(.+)$/.exec(l);
    if (cm && cur) {
      if (/^(окпд|ктру)/i.test(cm[1])) {
        if (/окпд/i.test(cm[1])) cur.окпд2 = cm[2].trim(); else cur.ктру = cm[2].trim();
        continue;
      }
      if (/^количеств/i.test(cm[1])) {
        const q = /(\d+(?:[.,]\d+)?)\s*(\S+)?/.exec(cm[2]);
        if (q) { cur.количество = Number(q[1].replace(',', '.')); cur.единица = q[2] || 'шт'; }
        continue;
      }
      cur.характеристики.push({ имя: cm[1].trim(), ...parseCondition(cm[2]) });
    }
  }
  return out;
}

export const SAMPLE_TZ = `Описание объекта закупки (пример для демо)

1. Ноутбук — 5 шт
ОКПД2: 26.20.11.110
Диагональ экрана: не менее 15.6 дюйм
Объём оперативной памяти: не менее 16 ГБ
Объём накопителя SSD: не менее 512 ГБ
Масса: не более 2 кг

2. Монитор — 5 шт
Диагональ: не менее 27 дюйм
Тип матрицы: IPS
Разрешение: не менее 2560x1440
Регулировка по высоте: да

3. IP-телефон — 20 шт
Количество SIP-линий: не менее 4
Питание по PoE: да

4. Шредер — 2 шт
Уровень секретности: не ниже P-4`;
