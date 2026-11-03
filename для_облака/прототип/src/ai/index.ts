// Слой ИИ: один интерфейс, два режима.
//  - «демо» (по умолчанию): работает без ключей и без сети — простые правила (rules.ts)
//    или заранее подготовленные результаты сверки;
//  - «живой»: вызов Claude API (live.ts), включается переменной окружения VITE_ANTHROPIC_API_KEY.
// Экран не знает, какой режим внутри: он вызывает analyzeTz() и показывает результат в формате блока G.

import type { CatalogItem, Sverka } from '../types';
import { parseTzText, matchPosition, tally } from './rules';
import { analyzeLive, liveKey } from './live';

export type AiMode = 'демо' | 'живой';

export function liveAvailable(): boolean {
  return Boolean(liveKey());
}

const PREF = 'tpk_ai_mode';

export function getMode(): AiMode {
  if (!liveAvailable()) return 'демо';
  try {
    return (localStorage.getItem(PREF) as AiMode) === 'демо' ? 'демо' : 'живой';
  } catch {
    return 'живой';
  }
}

export function setMode(m: AiMode) {
  try { localStorage.setItem(PREF, m); } catch { /* приватный режим браузера — не страшно */ }
}

export async function analyzeTz(tzText: string, catalog: CatalogItem[], base?: Partial<Sverka['закупка']>): Promise<Sverka> {
  if (getMode() === 'живой') return analyzeLive(tzText, catalog, base);
  // Демо: правила. Небольшая пауза — чтобы было видно, что идёт работа.
  await new Promise((r) => setTimeout(r, 450));
  const raw = parseTzText(tzText);
  const позиции = raw.map((p) => ({ ...p, сверка: matchPosition(p, catalog) }));
  return {
    закупка: {
      номер: base?.номер || '', предмет: base?.предмет || 'Техзадание из вставленного текста', заказчик: base?.заказчик || '',
      инн_заказчика: base?.инн_заказчика || '', закон: base?.закон || '', способ: base?.способ || '', нмц: base?.нмц || 0,
      регион: base?.регион || '', дата_окончания: base?.дата_окончания || '', ссылка: '',
      источник_документа: 'текст вставлен пользователем; разбор по простым правилам (демо-режим)',
    },
    позиции,
    итог: tally(позиции),
    режим: 'демо',
  };
}
