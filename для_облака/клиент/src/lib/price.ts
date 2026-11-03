import type { PriceRow } from './data';
import { priceTable } from './data';
import type { Tender } from '../types';

export const PARTS = ['1', '2', '3–4', '5+'] as const;
export type Parts = (typeof PARTS)[number];

// Ниши снимка → ниши таблицы цены. Для «Компьютеров и оргтехники» в таблице нет своей ниши:
// берём ближайшую по товару (электроника) и честно говорим об этом в интерфейсе.
const NICHE_MAP: Record<string, { name: string; approx: boolean }> = {
  'Связь и сети': { name: 'Связь, аудио- и видеотехника', approx: false },
  'Аудио- и видеотехника': { name: 'Связь, аудио- и видеотехника', approx: false },
  'Измерительные приборы': { name: 'Измерительные и лабораторные приборы', approx: false },
  'Лабораторные реактивы': { name: 'Измерительные и лабораторные приборы', approx: true },
  'Компьютеры и оргтехника': { name: 'Связь, аудио- и видеотехника', approx: true },
};

export function methodKey(m: string): string {
  const s = m.toLowerCase();
  if (s.includes('котировок')) return 'Запрос котировок';
  if (s.includes('аукцион')) return 'Электронный аукцион';
  if (s.includes('конкурс')) return 'Открытый конкурс';
  if (s.includes('предложен')) return 'Запрос предложений';
  return 'Иной способ';
}

export interface PriceEstimate {
  parts: Parts;
  row: PriceRow;
  medianPct: number; p25Pct: number; p75Pct: number; n: number;
  approxNiche: boolean; nicheUsed: string; scope: string;
}

function rowsFor(niche: string, law: string, method: string): { rows: PriceRow[]; scope: string } {
  const by = (l: string, m: string) => priceTable.filter((r) => r.ниша === niche && r.закон === l && r.способ === m);
  const tries: [string, string, string][] = [
    [law, method, `${law}, ${method}`], [law, 'все', law], ['все', 'все', 'все закупки ниши'],
  ];
  for (const [l, m, label] of tries) {
    const rows = by(l, m);
    if (rows.some((r) => r.участников !== 'все' && r.n >= 15)) return { rows, scope: label };
  }
  return { rows: by('все', 'все'), scope: 'все закупки ниши' };
}

/** Участников по умолчанию: где набирается половина закупок ниши (по числу n в корзинах) */
export function defaultParts(t: Tender): Parts {
  const { name } = NICHE_MAP[t.ниша] || NICHE_MAP['Компьютеры и оргтехника'];
  const rows = priceTable.filter((r) => r.ниша === name && r.закон === 'все' && r.способ === 'все' && r.участников !== 'все');
  const total = rows.reduce((s, r) => s + r.n, 0);
  let cum = 0;
  for (const p of PARTS) {
    cum += rows.find((r) => r.участников === p)?.n || 0;
    if (total && cum >= total / 2) return p;
  }
  return '2';
}

export function estimate(t: Tender, parts: Parts): PriceEstimate | null {
  const m = NICHE_MAP[t.ниша] || NICHE_MAP['Компьютеры и оргтехника'];
  const { rows, scope } = rowsFor(m.name, t.закон, methodKey(t.способ));
  const row = rows.find((r) => r.участников === parts && r.n >= 5) || priceTable.find((r) => r.ниша === m.name && r.закон === 'все' && r.способ === 'все' && r.участников === parts);
  if (!row) return null;
  return { parts, row, medianPct: row['медиана_снижения_%'], p25Pct: row['p25_%'], p75Pct: row['p75_%'], n: row.n, approxNiche: m.approx, nicheUsed: m.name, scope };
}

export function priceAt(nmc: number, dropPct: number): number { return Math.round(nmc * (1 - dropPct / 100)); }
