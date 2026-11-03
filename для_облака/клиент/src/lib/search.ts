import type { Tender } from '../types';
import { regionByCode } from './data';

export type Scope = 'region' | 'fo' | 'all';
export type SumKey = 'lt300' | '300-3m' | '3-20m' | 'any';

export interface Need { niches: string[]; keywords: string; scope: Scope; sum: SumKey }
export interface CompanyRegion { regionCode: number | null }

export const SUMS: { key: SumKey; label: string; min: number; max: number }[] = [
  { key: 'lt300', label: 'до 300 тыс.', min: 0, max: 300_000 },
  { key: '300-3m', label: '300 тыс. – 3 млн', min: 300_000, max: 3_000_000 },
  { key: '3-20m', label: '3–20 млн', min: 3_000_000, max: 20_000_000 },
  { key: 'any', label: 'Любая', min: 0, max: Infinity },
];

export const MS_DAY = 86_400_000;

export function endTime(t: Tender): number { return new Date(t.окончание_подачи).getTime(); }

/** Сколько полных дней до окончания подачи (округляем вверх, не меньше 0) */
export function daysLeft(t: Tender, now = Date.now()): number {
  return Math.max(0, Math.ceil((endTime(t) - now) / MS_DAY));
}

export function keywordList(s: string): string[] {
  return s.toLowerCase().replace(/ё/g, 'е').split(/[,;\n]+/).map((x) => x.trim()).filter((x) => x.length >= 2);
}

/** Слово ключа — начало слова в тексте: «проектор» найдёт «проекторов» (по 5 первым буквам), «МФУ» — только целиком */
function kwHits(text: string, kws: string[]): number {
  const low = text.toLowerCase().replace(/ё/g, 'е');
  let n = 0;
  for (const k of kws) {
    const root = k.length > 5 ? k.slice(0, Math.max(5, k.length - 2)) : k;
    if (low.includes(root)) n++;
  }
  return n;
}

export function tenderText(t: Tender): string {
  return t.предмет + ' ' + (t.позиции || []).map((p) => p.наименование).join(' ');
}

const SOFT_RE = /(лиценз|программн|подписк|услуг|ремонт|монтаж|обслуживан|техническ[а-яё]+ поддержк|право (на )?заключен)/i;
const GOODS_RE = /(поставк|приобретен|закупк[аи]\s+(товар|оборудован|техник))/i;

export interface Ranked { t: Tender; score: number; days: number; kw: number }

export interface SearchOpts { need: Need; regionCode: number | null; now?: number }

export function searchTenders(all: Tender[], { need, regionCode, now = Date.now() }: SearchOpts): Ranked[] {
  const kws = keywordList(need.keywords);
  const my = regionByCode(regionCode);
  const sum = SUMS.find((s) => s.key === need.sum) || SUMS[3];
  const out: Ranked[] = [];
  for (const t of all) {
    if (t.тип === 'работы/услуги' || t.флаги.includes('работы/услуги')) continue;
    if (endTime(t) < now + MS_DAY) continue; // подача заканчивается раньше чем через 24 часа
    if (need.niches.length && !need.niches.includes(t.ниша)) continue;
    const kw = kws.length ? kwHits(tenderText(t), kws) : 0;
    if (kws.length && kw === 0) continue;
    if (t.нмц < sum.min || t.нмц > sum.max) continue;
    const reg = regionByCode(t.регион_код);
    if (need.scope === 'region' && my && t.регион_код !== my.код) continue;
    if (need.scope === 'fo' && my && (!reg || reg.фо !== my.фо)) continue;
    const days = daysLeft(t, now);
    let score = kw * 3;
    if (SOFT_RE.test(t.предмет)) score -= 4; // лицензии, ПО, услуги, ремонт: не наш товар
    if (GOODS_RE.test(t.предмет)) score += 1;
    if (t.позиции && t.позиции.length) score += 2; // можно сверить по позициям
    if (days >= 3 && days <= 14) score += 2; else if (days > 14) score += 0.5; else score -= 0.5;
    if (my && t.регион_код === my.код) score += 2;
    else if (my && reg && reg.фо === my.фо) score += 0.7;
    out.push({ t, score, days, kw });
  }
  return out.sort((a, b) => b.score - a.score || endTime(a.t) - endTime(b.t));
}
