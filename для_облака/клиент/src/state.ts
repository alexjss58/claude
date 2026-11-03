import { useCallback, useEffect, useRef, useState } from 'react';
import type { Item, TenderResult } from './types';
import type { Need } from './lib/search';
import { lsGet, lsRemove, lsSet } from './lib/storage';

export interface Company { name: string; inn: string; regionCode: number | null; eds: '' | 'да' | 'нет' | 'не знаю' }
export interface CatalogState { source: 'file' | 'text' | 'demo' | null; name: string; text: string; items: Item[] }
export interface Contact { value: string; consent: boolean; sent: boolean }

export interface AppState {
  v: 1;
  step: number; // 0 — старт, 1…6 — шаги
  company: Company;
  need: Need;
  /** ключ последнего поиска: анимацию «ищем» показываем только при новом запросе */
  searchKey: string;
  picked: string[] | null;
  catalog: CatalogState;
  ai: Record<string, TenderResult>;
  participants: Record<string, string>;
  costs: Record<string, string>;
  contact: Contact;
}

export const EMPTY: AppState = {
  v: 1, step: 0,
  company: { name: '', inn: '', regionCode: null, eds: '' },
  need: { niches: [], keywords: '', scope: 'region', sum: 'any' },
  searchKey: '', picked: null,
  catalog: { source: null, name: '', text: '', items: [] },
  ai: {}, participants: {}, costs: {},
  contact: { value: '', consent: false, sent: false },
};

const KEY = 'tpk.client.v1';

function load(): AppState {
  const raw = lsGet(KEY);
  if (!raw) return EMPTY;
  try {
    const d = JSON.parse(raw) as Partial<AppState>;
    if (!d || d.v !== 1) return EMPTY;
    return {
      ...EMPTY, ...d,
      company: { ...EMPTY.company, ...d.company },
      need: { ...EMPTY.need, ...d.need },
      catalog: { ...EMPTY.catalog, ...d.catalog },
      contact: { ...EMPTY.contact, ...d.contact },
    } as AppState;
  } catch { return EMPTY; }
}

export function useAppState() {
  const [state, setState] = useState<AppState>(load);
  const first = useRef(true);
  useEffect(() => {
    if (first.current) { first.current = false; return; }
    const full = JSON.stringify(state);
    // Большой прайс может не поместиться в localStorage: тогда храним всё, кроме товаров
    if (!lsSet(KEY, full)) lsSet(KEY, JSON.stringify({ ...state, catalog: { ...state.catalog, items: [] }, ai: {} }));
  }, [state]);
  const patch = useCallback((p: Partial<AppState> | ((s: AppState) => Partial<AppState>)) => {
    setState((s) => ({ ...s, ...(typeof p === 'function' ? p(s) : p) }));
  }, []);
  const reset = useCallback(() => { lsRemove(KEY); setState(EMPTY); }, []);
  return { state, patch, reset };
}
