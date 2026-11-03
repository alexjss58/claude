// Минимальное чтение .xlsx в браузере: распаковка ZIP (fflate, синхронно) + разбор XML (DOMParser).
// Без Web Worker — поэтому работает и когда сайт открыт из файла (file://), без сервера.
// Читает первый лист: текст, числа, общие строки (sharedStrings) и строки внутри ячеек (inlineStr).
// Формулы не пересчитывает — берёт сохранённое значение.

import { strFromU8, unzipSync } from 'fflate';

function xml(files: Record<string, Uint8Array>, path: string): Document | null {
  const f = files[path];
  return f ? new DOMParser().parseFromString(strFromU8(f), 'application/xml') : null;
}

function texts(el: Element): string {
  // Текст ячейки может быть разбит на несколько <t> (форматирование внутри строки)
  return Array.from(el.getElementsByTagName('t')).map((t) => t.textContent || '').join('');
}

function colIndex(ref: string): number {
  const letters = /^[A-Z]+/.exec(ref)?.[0] || 'A';
  let n = 0;
  for (const ch of letters) n = n * 26 + (ch.charCodeAt(0) - 64);
  return n - 1;
}

/** Путь к первому листу по workbook.xml и его связям; запасной вариант — sheet1.xml */
function firstSheetPath(files: Record<string, Uint8Array>): { path: string; name: string; count: number } {
  const wb = xml(files, 'xl/workbook.xml');
  const rels = xml(files, 'xl/_rels/workbook.xml.rels');
  const sheets = wb ? Array.from(wb.getElementsByTagName('sheet')) : [];
  const first = sheets[0];
  if (first && rels) {
    const rid = first.getAttribute('r:id') || first.getAttributeNS('http://schemas.openxmlformats.org/officeDocument/2006/relationships', 'id');
    const rel = Array.from(rels.getElementsByTagName('Relationship')).find((r) => r.getAttribute('Id') === rid);
    const target = rel?.getAttribute('Target');
    if (target) {
      const path = target.startsWith('/') ? target.slice(1) : 'xl/' + target.replace(/^\.\//, '');
      if (files[path]) return { path, name: first.getAttribute('name') || 'Лист 1', count: sheets.length };
    }
  }
  return { path: 'xl/worksheets/sheet1.xml', name: first?.getAttribute('name') || 'Лист 1', count: sheets.length || 1 };
}

export interface XlsxResult { rows: string[][]; sheetName: string; sheetCount: number }

export function readXlsx(buf: ArrayBuffer): XlsxResult {
  let files: Record<string, Uint8Array>;
  try {
    files = unzipSync(new Uint8Array(buf), { filter: (f) => f.name.startsWith('xl/') && f.name.endsWith('.xml') || f.name.endsWith('.rels') });
  } catch {
    throw new Error('Файл не похож на .xlsx (не удалось распаковать). Сохраните его в Excel как «Книга Excel (.xlsx)».');
  }
  const shared: string[] = [];
  const ss = xml(files, 'xl/sharedStrings.xml');
  if (ss) for (const si of Array.from(ss.getElementsByTagName('si'))) shared.push(texts(si));
  const { path, name, count } = firstSheetPath(files);
  const sheet = xml(files, path);
  if (!sheet) throw new Error('В файле не нашли лист с данными.');
  const rows: string[][] = [];
  for (const row of Array.from(sheet.getElementsByTagName('row'))) {
    const r = Number(row.getAttribute('r') || rows.length + 1) - 1;
    const cells: string[] = [];
    for (const c of Array.from(row.getElementsByTagName('c'))) {
      const i = colIndex(c.getAttribute('r') || '');
      const t = c.getAttribute('t');
      const v = c.getElementsByTagName('v')[0]?.textContent ?? '';
      let val = '';
      if (t === 's') val = shared[Number(v)] ?? '';
      else if (t === 'inlineStr') val = texts(c);
      else if (t === 'b') val = v === '1' ? 'да' : 'нет';
      else val = v;
      cells[i] = val.replace(/\s+/g, ' ').trim();
    }
    rows[r] = Array.from(cells, (x) => x ?? '');
  }
  return { rows: Array.from(rows, (x) => x ?? []), sheetName: name, sheetCount: count };
}
