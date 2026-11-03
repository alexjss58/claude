// Блок «Цена»: ожидаемое снижение по нише, закону, способу и числу участников (формат «H → F»).
// Таблица — из модуля цены (блок H), если он есть, иначе своя оценка по выгрузкам.

import type { NicheCode, PriceRow, TenderView } from '../types';
import { priceTable } from '../data';

const isNiche = (rowNiche: string, code: NicheCode) =>
  code === 'svyaz' ? /связ|аудио|видео/i.test(rowNiche) : /прибор/i.test(rowNiche);

const ALL = (v: string) => /^все/i.test(v.trim());

function methodMatch(rowMethod: string, method: string) {
  if (ALL(rowMethod)) return false;
  const a = rowMethod.toLowerCase(), b = method.toLowerCase();
  return a === b || (a.includes('конкурс') && b.includes('конкурс')) || (a.includes('котиров') && b.includes('котиров'))
    || (a.includes('аукцион') && b.includes('аукцион')) || (a.includes('предложен') && b.includes('предложен'))
    || (a.includes('иной') && b.includes('иной'));
}

/** Подходит ли корзина участников: «1», «2», «3», «3–4», «4+», «5+» */
function partMatch(bucket: string, n: number) {
  const b = bucket.replace('—', '–').trim();
  if (ALL(b)) return false;
  if (/^\d+$/.test(b)) return Number(b) === n;
  const plus = /^(\d+)\+$/.exec(b);
  if (plus) return n >= Number(plus[1]);
  const range = /^(\d+)[–-](\d+)$/.exec(b);
  if (range) return n >= Number(range[1]) && n <= Number(range[2]);
  return false;
}

export interface PriceLookup {
  row: PriceRow;
  level: string; // какая ячейка таблицы использована
}

/**
 * Ищем самую точную ячейку, где хватает данных (n ≥ 8).
 * participants — сколько участников ожидаем (в демо: сколько было в этой закупке или медиана у заказчика).
 */
export function lookupPrice(niche: NicheCode, law: string, method: string, participants: number | null): PriceLookup | null {
  const rows = priceTable.filter((r) => isNiche(r.ниша, niche));
  const lawOk = (r: PriceRow) => r.закон === law;
  const lawAll = (r: PriceRow) => ALL(r.закон);
  const n = participants ?? null;
  const steps: [string, (r: PriceRow) => boolean][] = [];
  if (n !== null) {
    steps.push(['ниша × закон × способ × участники', (r) => lawOk(r) && methodMatch(r.способ, method) && partMatch(r.участников, n)]);
    steps.push(['ниша × закон × участники', (r) => lawOk(r) && ALL(r.способ) && partMatch(r.участников, n)]);
    steps.push(['ниша × участники', (r) => lawAll(r) && ALL(r.способ) && partMatch(r.участников, n)]);
  }
  steps.push(['ниша × закон × способ', (r) => lawOk(r) && methodMatch(r.способ, method) && ALL(r.участников)]);
  steps.push(['ниша × закон', (r) => lawOk(r) && ALL(r.способ) && ALL(r.участников)]);
  steps.push(['ниша', (r) => lawAll(r) && ALL(r.способ) && ALL(r.участников)]);
  for (const [level, f] of steps) {
    const row = rows.filter(f).sort((a, b) => b.n - a.n)[0];
    if (row && row.n >= 8) return { row, level };
  }
  for (const [level, f] of steps) {
    const row = rows.filter(f)[0];
    if (row) return { row, level: level + ' (мало данных)' };
  }
  return null;
}

/** Ожидаемое число участников: из закупки (если завершена) или медиана у заказчика, иначе 2 */
export function expectedParticipants(t: TenderView): { n: number; why: string } {
  if (t.участников) return { n: t.участников, why: 'столько было в этой закупке' };
  const h = t.история_заказчика?.медиана_участников;
  if (h) return { n: Math.round(h), why: 'медиана у этого заказчика' };
  return { n: 2, why: 'типичное значение по выгрузке (медиана — 2)' };
}

export interface PriceProposal {
  low: number; // цена при сильном снижении (p75)
  mid: number; // медиана
  high: number; // цена при слабом снижении (p25)
}

export function proposal(nmc: number, row: PriceRow): PriceProposal {
  return {
    low: nmc * (1 - row['p75_%'] / 100),
    mid: nmc * (1 - row['медиана_снижения_%'] / 100),
    high: nmc * (1 - row['p25_%'] / 100),
  };
}
