// Общее состояние: ассортимент поставщика и настройки показа.
// Хранится в localStorage — только в этом браузере, никуда не отправляется.

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import type { CatalogItem } from './types';
import { analyzeRows, buildCatalog, parseCsvText } from './lib/catalog';
import { samplePriceCsv } from './data';

const KEY_CATALOG = 'tpk_catalog_v1';
const KEY_SCALE = 'tpk_scale';

function load<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}
function save(key: string, v: unknown) {
  try { localStorage.setItem(key, JSON.stringify(v)); } catch { /* нет доступа к хранилищу — работаем без сохранения */ }
}

export const sampleCatalog: CatalogItem[] = buildCatalog(analyzeRows('пример_прайса_оргтехники.csv', parseCsvText(samplePriceCsv)));

interface Stored { items: CatalogItem[]; source: string; isSample: boolean }

interface Ctx {
  catalog: CatalogItem[];
  catalogSource: string;
  isSample: boolean;
  setCatalog: (items: CatalogItem[], source: string) => void;
  resetCatalog: () => void;
  scale: number;
  setScale: (n: number) => void;
}

const AppCtx = createContext<Ctx | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [stored, setStored] = useState<Stored>(() => load<Stored>(KEY_CATALOG, { items: sampleCatalog, source: 'пример_прайса_оргтехники.csv (демо)', isSample: true }));
  const [scale, setScaleState] = useState<number>(() => load<number>(KEY_SCALE, 1));

  useEffect(() => {
    document.documentElement.style.setProperty('--scale', String(scale));
  }, [scale]);

  const value = useMemo<Ctx>(() => ({
    catalog: stored.items.length ? stored.items : sampleCatalog,
    catalogSource: stored.source,
    isSample: stored.isSample,
    setCatalog: (items, source) => {
      const s = { items, source, isSample: false };
      setStored(s);
      save(KEY_CATALOG, s);
    },
    resetCatalog: () => {
      const s = { items: sampleCatalog, source: 'пример_прайса_оргтехники.csv (демо)', isSample: true };
      setStored(s);
      save(KEY_CATALOG, s);
    },
    scale,
    setScale: (n) => { setScaleState(n); save(KEY_SCALE, n); },
  }), [stored, scale]);

  return <AppCtx.Provider value={value}>{children}</AppCtx.Provider>;
}

export function useApp(): Ctx {
  const c = useContext(AppCtx);
  if (!c) throw new Error('AppProvider не подключён');
  return c;
}
