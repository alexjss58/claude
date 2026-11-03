// Общее состояние: ассортимент поставщика и настройки показа.
// Хранится в localStorage — только в этом браузере, никуда не отправляется.

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import type { CatalogItem } from './types';
import { analyzeRows, buildCatalog, parseCsvText } from './lib/catalog';
import { engineCatalog, samplePriceCsv } from './data';

const KEY_CATALOG = 'tpk_catalog_v2';
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

export const sampleCatalog: CatalogItem[] = buildCatalog(analyzeRows('пример прайса оргтехники', parseCsvText(samplePriceCsv)));

/** Откуда ассортимент: демо-каталог движка (по умолчанию, по нему сделана сверка), пример прайса или файл пользователя */
export type CatalogKind = 'движок' | 'пример' | 'свой';

const ENGINE_AVAILABLE = engineCatalog.length > 0;
const DEFAULT_KIND: CatalogKind = ENGINE_AVAILABLE ? 'движок' : 'пример';
export const SOURCE_LABEL: Record<CatalogKind, string> = {
  движок: `демо-каталог движка сверки: ${engineCatalog.length} реальных моделей, цен нет`,
  пример: 'пример прайса оргтехники (47 позиций, цены условные)',
  свой: 'ваш файл',
};

interface Stored { kind: CatalogKind; items?: CatalogItem[]; source?: string }

interface Ctx {
  catalog: CatalogItem[];
  catalogSource: string;
  catalogKind: CatalogKind;
  /** true, если это встроенный каталог, а не файл пользователя */
  isSample: boolean;
  /** true, если ассортимент тот же, по которому движок делал сверку */
  isEngineCatalog: boolean;
  setCatalog: (items: CatalogItem[], source: string) => void;
  useBuiltin: (kind: 'движок' | 'пример') => void;
  scale: number;
  setScale: (n: number) => void;
}

const AppCtx = createContext<Ctx | null>(null);

const builtin = (kind: CatalogKind): CatalogItem[] => (kind === 'движок' ? engineCatalog : sampleCatalog);

export function AppProvider({ children }: { children: ReactNode }) {
  const [stored, setStored] = useState<Stored>(() => {
    const st = load<Stored>(KEY_CATALOG, { kind: DEFAULT_KIND });
    if (st.kind === 'свой' && !(st.items && st.items.length)) return { kind: DEFAULT_KIND };
    if (st.kind === 'движок' && !ENGINE_AVAILABLE) return { kind: 'пример' };
    return st;
  });
  const [scale, setScaleState] = useState<number>(() => load<number>(KEY_SCALE, 1));

  useEffect(() => {
    document.documentElement.style.setProperty('--scale', String(scale));
  }, [scale]);

  const value = useMemo<Ctx>(() => ({
    catalog: stored.kind === 'свой' ? stored.items! : builtin(stored.kind),
    catalogSource: stored.kind === 'свой' ? stored.source || 'ваш файл' : SOURCE_LABEL[stored.kind],
    catalogKind: stored.kind,
    isSample: stored.kind !== 'свой',
    isEngineCatalog: stored.kind === 'движок',
    setCatalog: (items, source) => {
      const st: Stored = { kind: 'свой', items, source };
      setStored(st);
      save(KEY_CATALOG, st);
    },
    useBuiltin: (kind) => {
      const st: Stored = { kind };
      setStored(st);
      save(KEY_CATALOG, st);
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
