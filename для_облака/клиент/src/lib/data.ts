import snapshotRaw from '../data/snapshot.json';
import regionsRaw from '../data/regions.json';
import priceRaw from '../data/price.json';
import type { Region, Snapshot, Tender } from '../types';

export const snapshot = snapshotRaw as unknown as Snapshot;
export const regions = (regionsRaw as unknown as Region[]).slice().sort((a, b) => a.название.localeCompare(b.название, 'ru'));
export const priceTable = priceRaw as unknown as PriceRow[];

export interface PriceRow {
  ниша: string; закон: string; способ: string; участников: string;
  'медиана_снижения_%': number; 'p25_%': number; 'p75_%': number; n: number;
}

export const NICHES = ['Компьютеры и оргтехника', 'Связь и сети', 'Аудио- и видеотехника', 'Измерительные приборы', 'Лабораторные реактивы'];

export function regionByCode(code: number | null | undefined): Region | undefined {
  return code == null ? undefined : regions.find((r) => r.код === code);
}

export function tenderByNumber(n: string): Tender | undefined {
  return snapshot.тендеры.find((t) => t.номер === n);
}
