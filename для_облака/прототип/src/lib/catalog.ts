// Разбор прайса поставщика: CSV или XLSX → строки → поиск шапки → сопоставление столбцов → ассортимент.
// Всё работает в браузере, файл никуда не отправляется.

import Papa from 'papaparse';
import type { CatalogItem } from '../types';
import { parseNumber } from './format';

export type FieldKey =
  | 'артикул' | 'наименование' | 'категория' | 'производитель' | 'модель'
  | 'характеристики' | 'страна' | 'цена' | 'остаток' | 'примечание' | 'пропустить';

export const FIELD_LABELS: Record<FieldKey, string> = {
  артикул: 'Артикул / код',
  наименование: 'Наименование',
  категория: 'Категория',
  производитель: 'Производитель',
  модель: 'Модель',
  характеристики: 'Характеристики',
  страна: 'Страна происхождения',
  цена: 'Цена',
  остаток: 'Остаток',
  примечание: 'Примечание',
  пропустить: '— не использовать —',
};

const SYNONYMS: Record<Exclude<FieldKey, 'пропустить'>, string[]> = {
  артикул: ['артикул', 'код', 'sku', 'арт', 'код товара', 'part number', 'p/n', 'pn', 'партномер'],
  наименование: ['наименование', 'название', 'товар', 'номенклатура', 'name', 'наименование товара', 'позиция'],
  категория: ['категория', 'группа', 'тип товара', 'вид', 'раздел', 'подгруппа', 'класс'],
  производитель: ['производитель', 'бренд', 'марка', 'vendor', 'brand', 'изготовитель', 'вендор'],
  модель: ['модель', 'model'],
  характеристики: ['характеристики', 'описание', 'параметры', 'спецификация', 'технические характеристики', 'тех. характеристики', 'specs', 'свойства'],
  страна: ['страна', 'страна происхождения', 'страна производства', 'country', 'происхождение'],
  цена: ['цена', 'стоимость', 'price', 'цена закупки', 'опт', 'цена, руб', 'руб', 'цена с ндс', 'цена без ндс'],
  остаток: ['остаток', 'наличие', 'кол-во', 'количество', 'склад', 'stock', 'свободно'],
  примечание: ['примечание', 'комментарий', 'note', 'заметки'],
};

export interface ColumnGuess {
  index: number;
  header: string;
  field: FieldKey;
  confidence: 'точно' | 'вероятно' | 'не найдено';
  sample: string;
}

export interface ParsedSheet {
  fileName: string;
  rows: string[][];
  headerRow: number; // индекс строки с шапкой
  columns: ColumnGuess[];
  notes: string[];
}

function cellToString(v: unknown): string {
  if (v === null || v === undefined) return '';
  if (v instanceof Date) return v.toLocaleDateString('ru-RU');
  return String(v).replace(/\s+/g, ' ').trim();
}

/** Текст CSV: пробуем UTF-8, при «кракозябрах» — Windows-1251 (так часто сохраняет Excel). */
async function readText(file: File): Promise<{ text: string; enc: string }> {
  const buf = await file.arrayBuffer();
  const utf = new TextDecoder('utf-8').decode(buf);
  const bad = (utf.match(/�/g) || []).length;
  if (bad > 3) return { text: new TextDecoder('windows-1251').decode(buf), enc: 'Windows-1251' };
  return { text: utf.replace(/^﻿/, ''), enc: 'UTF-8' };
}

export function parseCsvText(text: string): string[][] {
  const res = Papa.parse<string[]>(text.replace(/^﻿/, ''), { skipEmptyLines: 'greedy', delimiter: '' });
  return (res.data || []).map((r) => r.map(cellToString));
}

export async function readFileRows(file: File): Promise<{ rows: string[][]; notes: string[] }> {
  const name = file.name.toLowerCase();
  const notes: string[] = [];
  if (name.endsWith('.xlsx')) {
    // Версия «universal» — без Web Worker: из file:// воркеры не запускаются, а сайт должен работать без сервера.
    const { default: readXlsxFile } = await import('read-excel-file/universal');
    const sheets = await readXlsxFile(await file.arrayBuffer());
    const first = sheets[0];
    if (sheets.length > 1) notes.push(`В файле ${sheets.length} листа(ов), взят первый: «${first.sheet}».`);
    return { rows: first.data.map((r) => r.map(cellToString)), notes };
  }
  if (name.endsWith('.xls')) {
    throw new Error('Старый формат .xls не поддерживается в прототипе. Сохраните файл как .xlsx или .csv.');
  }
  const { text, enc } = await readText(file);
  notes.push(`Кодировка файла: ${enc}.`);
  return { rows: parseCsvText(text), notes };
}

/** Строка шапки — первая из первых 15, где ≥ 3 непустых текстовых ячейки и больше половины совпадают со словарём. */
export function findHeaderRow(rows: string[][]): number {
  let best = 0, bestScore = -1;
  for (let i = 0; i < Math.min(rows.length, 15); i++) {
    const cells = rows[i].filter((c) => c);
    if (cells.length < 3) continue;
    const textual = cells.filter((c) => !/^[\d\s.,₽-]+$/.test(c)).length;
    const known = cells.filter((c) => guessField(c).confidence !== 'не найдено').length;
    const score = known * 3 + textual - (cells.some((c) => c.length > 60) ? 5 : 0);
    if (score > bestScore) { best = i; bestScore = score; }
  }
  return best;
}

function norm(s: string) {
  return s.toLowerCase().replace(/ё/g, 'е').replace(/[«»"'()*:]/g, '').replace(/\s+/g, ' ').trim();
}

function guessField(header: string): { field: FieldKey; confidence: ColumnGuess['confidence'] } {
  const h = norm(header);
  if (!h) return { field: 'пропустить', confidence: 'не найдено' };
  for (const [field, words] of Object.entries(SYNONYMS) as [FieldKey, string[]][]) {
    if (words.some((w) => h === w)) return { field, confidence: 'точно' };
  }
  for (const [field, words] of Object.entries(SYNONYMS) as [FieldKey, string[]][]) {
    if (words.some((w) => h.startsWith(w) || (w.length > 3 && h.includes(w)))) return { field, confidence: 'вероятно' };
  }
  return { field: 'пропустить', confidence: 'не найдено' };
}

/** По содержимому: числа > 100 — похоже на цену; «ГБ», «дюйм», «:» — на характеристики. */
function guessByContent(values: string[]): FieldKey | null {
  const v = values.filter(Boolean).slice(0, 30);
  if (!v.length) return null;
  const nums = v.map(parseNumber).filter((n): n is number => n !== null);
  if (nums.length / v.length > 0.8 && nums.some((n) => n >= 100)) return 'цена';
  if (v.filter((x) => /(гб|дюйм|вт|ва|стр\/мин|:)/i.test(x)).length / v.length > 0.6 && v.some((x) => x.length > 25)) return 'характеристики';
  return null;
}

export function analyzeRows(fileName: string, rows: string[][], extraNotes: string[] = []): ParsedSheet {
  const headerRow = findHeaderRow(rows);
  const header = rows[headerRow] || [];
  const body = rows.slice(headerRow + 1).filter((r) => r.some(Boolean));
  const width = Math.max(header.length, ...body.slice(0, 50).map((r) => r.length));
  const used = new Set<FieldKey>();
  const columns: ColumnGuess[] = [];
  for (let i = 0; i < width; i++) {
    const h = header[i] || '';
    let { field, confidence } = guessField(h);
    if (field !== 'пропустить' && used.has(field)) { field = 'пропустить'; confidence = 'не найдено'; }
    if (field === 'пропустить') {
      const byContent = guessByContent(body.map((r) => r[i] || ''));
      if (byContent && !used.has(byContent)) { field = byContent; confidence = 'вероятно'; }
    }
    if (field !== 'пропустить') used.add(field);
    columns.push({ index: i, header: h || `Столбец ${i + 1}`, field, confidence, sample: body.find((r) => r[i])?.[i] || '' });
  }
  const notes = [...extraNotes];
  if (headerRow > 0) notes.push(`Шапка таблицы найдена в строке ${headerRow + 1}; строки выше — заголовок файла, они пропущены.`);
  if (!used.has('наименование')) notes.push('Не нашли столбец с наименованием — выберите его вручную.');
  if (!used.has('цена')) notes.push('Не нашли столбец с ценой — без него не посчитать маржу.');
  return { fileName, rows, headerRow, columns, notes };
}

/** «Процессор: i5; ОЗУ: 8 ГБ» → { Процессор: 'i5', ОЗУ: '8 ГБ' } */
export function parseSpecs(text: string): Record<string, string> {
  const out: Record<string, string> = {};
  if (!text) return out;
  for (const part of text.split(/[;\n|]+/)) {
    const m = /^\s*([^:=]{2,60})[:=]\s*(.+?)\s*$/.exec(part);
    if (m) out[m[1].trim()] = m[2].trim();
  }
  return out;
}

const CATEGORY_BY_NAME: [RegExp, string][] = [
  [/ноутбук/i, 'Ноутбук'], [/моноблок/i, 'Моноблок'], [/(системн\w* блок|компьютер|неттоп|пк\b)/i, 'Системный блок'],
  [/монитор/i, 'Монитор'], [/мфу/i, 'МФУ'], [/принтер/i, 'Принтер'], [/сканер/i, 'Сканер'],
  [/(ибп|бесперебойн|ups)/i, 'ИБП'], [/коммутатор/i, 'Коммутатор'], [/(маршрутизатор|роутер|интернет-центр)/i, 'Маршрутизатор'],
  [/ip-телефон/i, 'IP-телефон'], [/(dect|беспроводн\w* трубк)/i, 'Телефон DECT'], [/телефон/i, 'Телефон'],
  [/гарнитур|наушник/i, 'Гарнитура'], [/веб-?камер/i, 'Веб-камера'], [/проектор/i, 'Проектор'],
  [/радиосистем|микрофон/i, 'Радиосистема'], [/микшер/i, 'Микшерный пульт'], [/(акустич|колонк)/i, 'Акустическая система'],
  [/телевизор/i, 'Телевизор'], [/(радиостанц|рация)/i, 'Радиостанция'], [/планшет/i, 'Планшет'],
];

// Аксессуар «для IP-телефона» — не IP-телефон: если название начинается с такого слова, категорию не угадываем.
const ACCESSORY_RE = /^\s*(консол|кронштейн|кабел|картридж|тонер|блок\w* питани|сумк|чехол|адаптер|переходник|креплени|держател|запчаст|комплектующ|лицензи)/i;

export function categoryFromName(name: string): string {
  if (ACCESSORY_RE.test(name)) return 'Прочее';
  for (const [re, c] of CATEGORY_BY_NAME) if (re.test(name)) return c;
  return 'Прочее';
}

export function buildCatalog(parsed: ParsedSheet): CatalogItem[] {
  const col = (f: FieldKey) => parsed.columns.find((c) => c.field === f)?.index;
  const idx = {
    артикул: col('артикул'), наименование: col('наименование'), категория: col('категория'),
    производитель: col('производитель'), модель: col('модель'), характеристики: col('характеристики'),
    страна: col('страна'), цена: col('цена'), остаток: col('остаток'),
  };
  const get = (r: string[], i: number | undefined) => (i === undefined ? '' : r[i] || '');
  const items: CatalogItem[] = [];
  parsed.rows.slice(parsed.headerRow + 1).forEach((r, n) => {
    const name = get(r, idx.наименование) || [get(r, idx.производитель), get(r, idx.модель)].filter(Boolean).join(' ');
    if (!name) return;
    const specText = get(r, idx.характеристики);
    items.push({
      артикул: get(r, idx.артикул) || `стр-${parsed.headerRow + n + 2}`,
      наименование: name,
      категория: get(r, idx.категория) || categoryFromName(name),
      производитель: get(r, idx.производитель),
      модель: get(r, idx.модель),
      характеристики: parseSpecs(specText),
      характеристики_текст: specText,
      страна: get(r, idx.страна),
      цена: parseNumber(get(r, idx.цена)),
      остаток: parseNumber(get(r, idx.остаток)),
    });
  });
  return items;
}
