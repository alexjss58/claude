// Разбор ассортимента: Excel / CSV / вставленный текст / демо-каталог → список товаров.
// Всё работает в браузере, файл никуда не отправляется.
// Столбцы определяются автоматически (по заголовкам и по содержимому). Все «лишние» столбцы с данными
// считаются характеристиками товара: так читается и широкий прайс с десятками колонок.

import Papa from 'papaparse';
import type { Item } from '../types';
import { parseNumber } from './format';
import { readXlsx } from './xlsx';

export type FieldKey = 'артикул' | 'наименование' | 'категория' | 'производитель' | 'модель' | 'характеристики' | 'цена' | 'остаток' | 'примечание' | 'пропустить' | 'свойство';

export const FIELD_LABELS: Record<FieldKey, string> = {
  артикул: 'Артикул', наименование: 'Наименование', категория: 'Категория', производитель: 'Производитель', модель: 'Модель',
  характеристики: 'Характеристики (текст)', цена: 'Цена', остаток: 'Остаток', примечание: 'Примечание',
  пропустить: 'Не использовать', свойство: 'Характеристика',
};

const SYNONYMS: Record<Exclude<FieldKey, 'пропустить' | 'свойство'>, string[]> = {
  артикул: ['артикул', 'код', 'sku', 'арт', 'код товара', 'part number', 'p/n', 'pn', 'партномер'],
  наименование: ['наименование', 'название', 'товар', 'номенклатура', 'name', 'наименование товара', 'позиция'],
  категория: ['категория', 'группа', 'тип товара', 'вид', 'раздел', 'подгруппа', 'класс'],
  производитель: ['производитель', 'бренд', 'марка', 'vendor', 'brand', 'изготовитель', 'вендор'],
  модель: ['модель', 'model'],
  характеристики: ['характеристики', 'описание', 'параметры', 'спецификация', 'технические характеристики', 'specs', 'свойства'],
  цена: ['цена', 'стоимость', 'price', 'цена закупки', 'опт', 'цена, руб', 'руб', 'цена с ндс', 'цена без ндс'],
  остаток: ['остаток', 'наличие', 'кол-во', 'количество', 'склад', 'stock', 'свободно'],
  примечание: ['примечание', 'комментарий', 'note', 'заметки'],
};

// Служебные столбцы чужих выгрузок: характеристиками не считаем.
const SERVICE_COLUMN = /(источник|url|надежност|надёжност|дата проверки|реестр|окпд|страна)/i;

export interface ColumnGuess { index: number; header: string; field: FieldKey; sample: string }
export interface ParsedSheet { fileName: string; rows: string[][]; headerRow: number; columns: ColumnGuess[]; notes: string[] }

function cell(v: unknown): string {
  if (v === null || v === undefined) return '';
  return String(v).replace(/\s+/g, ' ').trim();
}

async function readText(file: File): Promise<string> {
  const buf = await file.arrayBuffer();
  const utf = new TextDecoder('utf-8').decode(buf);
  // «кракозябры» (символ замены U+FFFD): значит, файл в Windows-1251, как часто сохраняет Excel
  if ((utf.match(/\uFFFD/g) || []).length > 3) return new TextDecoder('windows-1251').decode(buf);
  return utf.replace(/^﻿/, '');
}

export function parseCsvText(text: string): string[][] {
  const res = Papa.parse<string[]>(text.replace(/^﻿/, ''), { skipEmptyLines: 'greedy', delimiter: '' });
  return (res.data || []).map((r) => r.map(cell));
}

export async function readFileRows(file: File): Promise<string[][]> {
  const name = file.name.toLowerCase();
  if (name.endsWith('.xlsx')) return readXlsx(await file.arrayBuffer()).rows;
  if (name.endsWith('.xls')) throw new Error('Старый формат .xls не читаем. Сохраните файл как .xlsx или .csv и загрузите снова.');
  return parseCsvText(await readText(file));
}

function norm(s: string) { return s.toLowerCase().replace(/ё/g, 'е').replace(/[«»"'()*:]/g, '').replace(/\s+/g, ' ').trim(); }

function guessField(header: string): { field: FieldKey; sure: boolean } {
  const h = norm(header);
  if (!h) return { field: 'пропустить', sure: false };
  for (const [f, words] of Object.entries(SYNONYMS) as [FieldKey, string[]][]) if (words.includes(h)) return { field: f, sure: true };
  for (const [f, words] of Object.entries(SYNONYMS) as [FieldKey, string[]][])
    if (words.some((w) => h.startsWith(w) || (w.length > 3 && h.includes(w)))) return { field: f, sure: false };
  return { field: 'пропустить', sure: false };
}

function findHeaderRow(rows: string[][]): number {
  let best = 0, bestScore = -1;
  for (let i = 0; i < Math.min(rows.length, 15); i++) {
    const cells = rows[i].filter(Boolean);
    if (cells.length < 3) continue;
    const textual = cells.filter((c) => !/^[\d\s.,₽-]+$/.test(c)).length;
    const known = cells.filter((c) => guessField(c).field !== 'пропустить').length;
    const score = known * 3 + textual - (cells.some((c) => c.length > 60) ? 5 : 0);
    if (score > bestScore) { best = i; bestScore = score; }
  }
  return best;
}

function looksPrice(values: string[]): boolean {
  const v = values.filter(Boolean).slice(0, 40);
  if (v.length < 2) return false;
  const nums = v.map(parseNumber).filter((n): n is number => n !== null);
  return nums.length / v.length > 0.85 && nums.filter((n) => n >= 100).length / v.length > 0.7;
}

export function analyzeRows(fileName: string, rows: string[][]): ParsedSheet {
  const headerRow = findHeaderRow(rows);
  const header = rows[headerRow] || [];
  const body = rows.slice(headerRow + 1).filter((r) => r.some(Boolean));
  const width = Math.max(header.length, ...body.slice(0, 50).map((r) => r.length), 0);
  const used = new Set<FieldKey>();
  const columns: ColumnGuess[] = [];
  for (let i = 0; i < width; i++) {
    const h = header[i] || '';
    const values = body.map((r) => r[i] || '');
    let { field } = guessField(h);
    if (field !== 'пропустить' && used.has(field)) field = 'пропустить';
    if (field === 'пропустить' && !used.has('цена') && looksPrice(values)) field = 'цена';
    // Свойство: есть заголовок и хоть что-то в столбце, и это не служебный столбец
    if (field === 'пропустить' && h && values.some(Boolean) && !SERVICE_COLUMN.test(h)) field = 'свойство';
    if (field !== 'пропустить' && field !== 'свойство') used.add(field);
    columns.push({ index: i, header: h || `Столбец ${i + 1}`, field, sample: values.find(Boolean) || '' });
  }
  // Нет столбца наименования: ищем самый «текстовый» среди свойств
  if (!used.has('наименование') && !(used.has('производитель') && used.has('модель'))) {
    let bestI = -1, bestLen = 0;
    for (const c of columns) {
      if (c.field !== 'свойство') continue;
      const vals = body.map((r) => r[c.index] || '').filter(Boolean);
      const avg = vals.reduce((s, x) => s + x.length, 0) / Math.max(1, vals.length);
      if (vals.length >= body.length * 0.8 && avg > 8 && !looksPrice(vals) && avg > bestLen) { bestI = c.index; bestLen = avg; }
    }
    if (bestI >= 0) columns[bestI].field = 'наименование';
  }
  return { fileName, rows, headerRow, columns, notes: [] };
}

export function needsManual(p: ParsedSheet): boolean {
  const has = (f: FieldKey) => p.columns.some((c) => c.field === f);
  return !has('наименование') && !(has('производитель') && has('модель'));
}

/** «Процессор: i5; ОЗУ: 8 ГБ» → { Процессор: 'i5', ОЗУ: '8 ГБ' } */
export function parseSpecs(text: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const part of (text || '').split(/[;\n|]+/)) {
    const m = /^\s*([^:=]{2,60})[:=]\s*(.+?)\s*$/.exec(part);
    if (m) out[m[1].trim()] = m[2].trim();
  }
  return out;
}

const NO_VALUE = /^(нет данных|н\/д|-|—|0 \(в перечне портов нет\))$/i;

export function buildItems(p: ParsedSheet): Item[] {
  const col = (f: FieldKey) => p.columns.find((c) => c.field === f)?.index;
  const iArt = col('артикул'), iName = col('наименование'), iCat = col('категория'), iBrand = col('производитель'), iModel = col('модель');
  const iTxt = col('характеристики'), iPrice = col('цена'), iNote = col('примечание');
  const props = p.columns.filter((c) => c.field === 'свойство');
  const g = (r: string[], i: number | undefined) => (i === undefined ? '' : r[i] || '');
  const items: Item[] = [];
  p.rows.slice(p.headerRow + 1).forEach((r, n) => {
    if (!r.some(Boolean)) return;
    const brand = g(r, iBrand), model = g(r, iModel), cat = g(r, iCat);
    let name = g(r, iName);
    if (!name) name = [cat ? (cat.length <= 4 ? cat.toUpperCase() : cat[0].toUpperCase() + cat.slice(1)) : '', brand, model].filter(Boolean).join(' ');
    if (!name) return;
    const specs: Record<string, string> = { ...parseSpecs(g(r, iTxt)) };
    for (const c of props) {
      const v = r[c.index] || '';
      if (v && !NO_VALUE.test(v)) specs[c.header] = v;
    }
    items.push({
      id: g(r, iArt) || `стр-${p.headerRow + n + 2}`, name, brand, model, category: cat,
      price: parseNumber(g(r, iPrice)), specs, note: g(r, iNote),
    });
  });
  return items;
}

/** Список текстом: «HP ProBook 450 G10 16/512 — 78 000», по товару на строку */
export function parseList(text: string): Item[] {
  const items: Item[] = [];
  text.split(/\r?\n/).forEach((raw, n) => {
    const line = raw.replace(/\s+/g, ' ').trim();
    if (line.length < 2) return;
    let name = line, price: number | null = null;
    const m = /^(.*?[A-Za-zА-Яа-яЁё\d)])\s*(?:[—–;|\t:]|\s-\s|\s)\s*(\d[\d\s.,]*)\s*(?:₽|руб\.?|р\.?)?$/.exec(line);
    if (m) {
      const num = parseNumber(m[2]);
      if (num !== null && num >= 100) { name = m[1].replace(/[—–;|:-]+$/, '').trim(); price = num; }
    }
    items.push({ id: `текст-${n + 1}`, name, brand: '', model: '', category: '', price, specs: {}, note: '' });
  });
  return items;
}

export async function loadFile(file: File): Promise<ParsedSheet> {
  const rows = await readFileRows(file);
  if (!rows.length) throw new Error('Файл пустой.');
  return analyzeRows(file.name, rows);
}

export function parseCsvString(name: string, text: string): ParsedSheet {
  return analyzeRows(name, parseCsvText(text));
}
