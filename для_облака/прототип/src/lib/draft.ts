// Черновик заявки: модель документа (для предпросмотра на экране) и выгрузка в .docx и .csv.
// Все тексты документов — ШАБЛОНЫ. Перед подачей их проверяет юрист. Не юридическая консультация.

import type { CatalogItem, Sverka, TenderView } from '../types';
import { findItem } from './match';
import { specValue } from '../ai/rules';

export const SUPPLIER = {
  name: 'ООО «Пример-Оргтехника» (демо-поставщик)',
  inn: '__________',
  head: '__________ (должность, ФИО)',
};

export interface DraftRow {
  n: number;
  позиция: string;
  товар: string;
  страна: string;
  количество: string;
  статус: string;
  характеристики: { имя: string; требование: string; значение: string }[];
}

export interface DraftModel {
  title: string;
  zakupka: { label: string; value: string }[];
  rows: DraftRow[];
  docs: { title: string; text: string[] }[];
  checklist: string[];
  warnings: string[];
}

function req(c: Sverka['позиции'][number]['характеристики'][number]) {
  const u = c.единица ? ` ${c.единица}` : '';
  const eq = c.эквивалент_допускается ? '' : ' (эквивалент не допускается)';
  switch (c.условие) {
    case '>=': return `не менее ${c.значение}${u}${eq}`;
    case '<=': return `не более ${c.значение}${u}${eq}`;
    case 'из_списка': return `одно из: ${c.значение}${eq}`;
    default: return `${c.значение}${u}${eq}`;
  }
}

export function buildDraft(t: TenderView, sverka: Sverka | undefined, catalog: CatalogItem[], price: number | null): DraftModel {
  const is44 = t.закон.includes('44');
  const rows: DraftRow[] = (sverka?.позиции || []).map((p) => {
    const item = findItem(catalog, p.сверка.артикул, p.сверка.товар_из_каталога);
    const bad = new Map(p.сверка.расхождения.map((r) => [r.характеристика, r.у_товара]));
    return {
      n: p['№'],
      позиция: p.наименование,
      товар: p.сверка.статус === 'нет' ? '— товар не подобран —' : (p.сверка.товар_из_каталога || '—'),
      страна: item?.страна || 'заполнить',
      количество: `${p.количество} ${p.единица}`,
      статус: p.сверка.статус,
      характеристики: p.характеристики.map((c) => ({
        имя: c.имя,
        требование: req(c),
        значение: p.сверка.статус === 'нет' ? '—'
          : bad.get(c.имя) ? `${bad.get(c.имя)} ⚠ не соответствует`
          : (item && specValue(item, c.имя)) || 'соответствует (по данным сверки) — сверить с паспортом товара',
      })),
    };
  });
  const no = rows.filter((r) => r.статус === 'нет').length;
  const almost = rows.filter((r) => r.статус === 'почти').length;
  const warnings: string[] = [];
  if (almost) warnings.push(`${almost} поз. «почти подходит»: подобрать другой товар или задать вопрос заказчику (запрос на разъяснение).`);
  if (no) warnings.push(`${no} поз. без товара: найти у дистрибьютора или не подавать заявку, если частичная поставка не допускается.`);
  if (!sverka) warnings.push('Для этой закупки нет сверки техзадания: таблица характеристик пустая. Загрузите техзадание в карточке тендера.');

  const docs = [
    {
      title: '1. Предложение участника о поставке товара (согласие)',
      text: [
        `Участник закупки ${SUPPLIER.name}, ИНН ${SUPPLIER.inn}, ознакомившись с извещением и документацией о закупке «${t.предмет}»${t.номер ? ` (№ ${t.номер})` : ''}, предлагает поставить товар в соответствии с описанием объекта закупки на условиях, предусмотренных извещением и проектом контракта.`,
        `Характеристики, товарные знаки (при наличии) и страна происхождения предлагаемого товара указаны в таблице «Предложение участника в отношении объекта закупки».`,
        price ? `Предложение о цене: ${Math.round(price).toLocaleString('ru-RU')} ₽ (черновик; цену подают на площадке в порядке, установленном извещением).` : 'Предложение о цене подаётся на площадке.',
      ],
    },
    {
      title: '2. Декларация о соответствии участника требованиям',
      text: [
        is44
          ? 'Участник декларирует соответствие единым требованиям, установленным пунктами 3–5, 7–11 части 1 статьи 31 Федерального закона № 44-ФЗ, а также отсутствие сведений об участнике в реестре недобросовестных поставщиков (пункт 12 части 1 статьи 31).'
          : 'Участник декларирует соответствие требованиям к участникам, установленным документацией о закупке и положением о закупке заказчика, и отсутствие сведений об участнике в реестрах недобросовестных поставщиков.',
        'Перечень пунктов зависит от извещения — сверить с требованиями конкретной закупки.',
      ],
    },
    {
      title: '3. Декларация о принадлежности к субъектам малого и среднего предпринимательства',
      text: [
        `Участник декларирует, что является субъектом малого предпринимательства в соответствии с Федеральным законом от 24.07.2007 № 209-ФЗ и сведения о нём содержатся в едином реестре субъектов малого и среднего предпринимательства.`,
        is44 ? 'Нужна, если закупка проводится только для СМП и СОНКО (статья 30 44-ФЗ).' : 'Нужна, если закупка проводится только для субъектов МСП (постановление Правительства РФ № 1352) — форма может быть установлена документацией.',
      ],
    },
    {
      title: '4. Сведения о стране происхождения и реестровых записях (нацрежим)',
      text: [
        'Для товаров, на которые распространяется национальный режим (постановление Правительства РФ от 23.12.2024 № 1875), указать номера реестровых записей из реестра российской промышленной продукции или реестра евразийской промышленной продукции (ГИСП), а для радиоэлектроники — из реестра российской радиоэлектронной продукции.',
        'Номера реестровых записей в черновике не заполнены — их подставляют после проверки каждого товара.',
      ],
    },
  ];
  const checklist = [
    'Электронная подпись руководителя или сотрудника с машиночитаемой доверенностью (МЧД).',
    'Аккредитация на площадке, где проводится закупка.',
    is44 ? 'Обеспечение заявки (если требуется): деньги на спецсчёте или независимая гарантия.' : 'Обеспечение заявки (если требуется документацией): способ — по документации.',
    'Номера реестровых записей для товаров под нацрежим.',
    'Проверить, что в таблице нет «⚠ не соответствует» и «заполнить».',
    'Юрист проверяет тексты деклараций и формы, если заказчик дал свои.',
  ];
  return {
    title: `Черновик заявки: ${t.предмет}`,
    zakupka: [
      { label: 'Закупка', value: t.номер ? `${t.номер} — ${t.предмет}` : t.предмет },
      { label: 'Заказчик', value: t.заказчик },
      { label: 'Закон, способ', value: `${t.закон}, ${t.способ}` },
      { label: 'НМЦ', value: t.нмц ? `${Math.round(t.нмц).toLocaleString('ru-RU')} ₽` : '—' },
      { label: 'Окончание подачи', value: t.дата_окончания },
      { label: 'Участник', value: SUPPLIER.name },
    ],
    rows,
    docs,
    checklist,
    warnings,
  };
}

function download(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

const TR: Record<string, string> = { а: 'a', б: 'b', в: 'v', г: 'g', д: 'd', е: 'e', ё: 'e', ж: 'zh', з: 'z', и: 'i', й: 'y', к: 'k', л: 'l', м: 'm', н: 'n', о: 'o', п: 'p', р: 'r', с: 's', т: 't', у: 'u', ф: 'f', х: 'h', ц: 'ts', ч: 'ch', ш: 'sh', щ: 'sch', ъ: '', ы: 'y', ь: '', э: 'e', ю: 'yu', я: 'ya' };

/** Имя файла латиницей: некоторые браузеры и системы теряют кириллицу в имени скачиваемого файла */
export function safeName(s: string) {
  const lat = s.toLowerCase().split('').map((ch) => (ch in TR ? TR[ch] : ch)).join('');
  return lat.replace(/[^a-z0-9-]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 50).replace(/_+$/, '') || 'zakupka';
}

export function downloadCsv(m: DraftModel, base: string) {
  const lines = [['№', 'Позиция по техзаданию', 'Предлагаемый товар', 'Характеристика', 'Требование заказчика', 'Значение у товара', 'Страна происхождения', 'Количество']];
  for (const r of m.rows) for (const c of r.характеристики) lines.push([String(r.n), r.позиция, r.товар, c.имя, c.требование, c.значение, r.страна, r.количество]);
  const csv = '﻿' + lines.map((l) => l.map((x) => `"${String(x).replace(/"/g, '""')}"`).join(';')).join('\r\n');
  download(new Blob([csv], { type: 'text/csv;charset=utf-8' }), `${base}_harakteristiki.csv`);
}

export async function downloadDocx(m: DraftModel, base: string) {
  const d = await import('docx');
  const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, HeadingLevel, AlignmentType, BorderStyle } = d;
  const font = 'Times New Roman';
  const p = (text: string, opts: { bold?: boolean; size?: number; color?: string; italics?: boolean; align?: (typeof AlignmentType)[keyof typeof AlignmentType] } = {}) =>
    new Paragraph({ alignment: opts.align, spacing: { after: 120 }, children: [new TextRun({ text, bold: opts.bold, size: opts.size ?? 22, color: opts.color, italics: opts.italics, font })] });
  const cell = (text: string, bold = false, shade?: string) => new TableCell({
    shading: shade ? { fill: shade } : undefined,
    children: [new Paragraph({ children: [new TextRun({ text, bold, size: 18, font })] })],
  });
  const border = { style: BorderStyle.SINGLE, size: 4, color: '1C1A17' };
  const tableRows = [new TableRow({ tableHeader: true, children: ['№', 'Позиция', 'Товар', 'Характеристика', 'Требование', 'Значение у товара', 'Страна'].map((h) => cell(h, true, 'EDE6D6')) })];
  for (const r of m.rows) {
    r.характеристики.forEach((c, i) => {
      tableRows.push(new TableRow({ children: [
        cell(i === 0 ? String(r.n) : ''), cell(i === 0 ? `${r.позиция} (${r.количество})` : ''), cell(i === 0 ? r.товар : ''),
        cell(c.имя), cell(c.требование), cell(c.значение), cell(i === 0 ? r.страна : ''),
      ] }));
    });
  }
  const children: (InstanceType<typeof Paragraph> | InstanceType<typeof Table>)[] = [
    p('ЧЕРНОВИК. Шаблоны документов — проверить юристом. Не юридическая консультация. Сформировано демо-версией «Тендер под ключ».', { bold: true, color: 'A3261B', size: 20 }),
    new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { after: 200 }, children: [new TextRun({ text: m.title, bold: true, size: 30, font })] }),
    ...m.zakupka.map((z) => p(`${z.label}: ${z.value}`)),
    new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 120 }, children: [new TextRun({ text: 'Предложение участника в отношении объекта закупки', bold: true, size: 26, font })] }),
  ];
  if (m.rows.length) {
    children.push(new Table({ width: { size: 100, type: WidthType.PERCENTAGE }, borders: { top: border, bottom: border, left: border, right: border, insideHorizontal: border, insideVertical: border }, rows: tableRows }));
  } else {
    children.push(p('Таблица характеристик не заполнена: нет сверки техзадания.', { italics: true }));
  }
  for (const doc of m.docs) {
    children.push(new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 280, after: 120 }, children: [new TextRun({ text: doc.title + ' — шаблон, проверить юристом', bold: true, size: 24, font })] }));
    for (const t of doc.text) children.push(p(t));
    children.push(p(`${SUPPLIER.head} ____________ (подпись)`, { italics: true }));
  }
  children.push(new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 280, after: 120 }, children: [new TextRun({ text: 'Что проверить перед подачей', bold: true, size: 24, font })] }));
  for (const c of [...m.warnings, ...m.checklist]) children.push(p('☐ ' + c));
  const doc = new Document({ creator: 'Тендер под ключ (демо)', title: m.title, sections: [{ children }] });
  const blob = await Packer.toBlob(doc);
  download(blob, `${base}_chernovik_zayavki.docx`);
}
