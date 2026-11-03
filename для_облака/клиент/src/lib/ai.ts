// Сверка с помощью Claude: runtime-возможность `sample` (страница открыта на claude.ai).
// Определения: artifact-capabilities/sample.d.ts. Один вызов на тендер; ответ — строгий JSON.
// Первый вызов спрашивает согласие у человека, поэтому запускаем только по нажатию кнопки.
// Возможность надо объявить при публикации: capabilities: { sample: {}, downloads: {} }.

import type { Item, PosResult, Position, Status, Tender, TenderResult } from '../types';
import { candidatesFor, matchTender, pseudoPositions, summarize } from './match';
import { runtime } from './save';

export type AiErrorKind = 'not_granted' | 'rate_limited' | 'other';
export class AiError extends Error {
  kind: AiErrorKind;
  constructor(kind: AiErrorKind, message: string) { super(message); this.kind = kind; }
}

interface Sample {
  json: <T = unknown>(input: string, options?: { modelTier?: string; signal?: AbortSignal }) => Promise<T>;
}

let cached: Promise<Sample | null> | null = null;

/** null — ИИ недоступен (страница не на claude.ai): работаем только правилами */
export function getSample(): Promise<Sample | null> {
  const c = runtime();
  if (!c) return Promise.resolve(null);
  if (!cached) cached = c.use('sample').then((s) => (s && typeof (s as Sample).json === 'function' ? (s as Sample) : null)).catch(() => null);
  return cached;
}

interface AiRow { '№'?: unknown; 'статус'?: unknown; 'товар'?: unknown; 'расхождения'?: unknown; 'комментарий'?: unknown }

const clip = (s: string, n: number) => (s.length > n ? s.slice(0, n - 1) + '…' : s);

function posPayload(p: Position, cands: Item[]) {
  return {
    '№': p['№'], 'наименование': p.наименование, 'окпд2': p.окпд2, 'количество': p.количество, 'единица': p.единица,
    'характеристики': p.характеристики.slice(0, 40).map((c) => `${c.имя} ${c.условие} ${c.значение}${c.единица ? ' ' + c.единица : ''}`),
    'кандидаты': cands.map((c) => c.id),
  };
}

function itemPayload(it: Item) {
  const specs = Object.entries(it.specs).slice(0, 45).map(([k, v]) => `${k}: ${clip(v, 60)}`);
  return { id: it.id, 'наименование': it.name, 'цена': it.price, 'характеристики': specs, ...(it.note ? { 'примечание': clip(it.note, 160) } : {}) };
}

export function buildPrompt(t: Tender, catalog: Item[]): { prompt: string; used: Map<string, Item> } {
  const noTz = !(t.позиции && t.позиции.length);
  const positions = (noTz ? pseudoPositions(t) : t.позиции!).slice(0, 25);
  const used = new Map<string, Item>();
  const posList = positions.map((p) => {
    const cands = candidatesFor(p, catalog, 10);
    cands.forEach((c) => used.set(c.id, c));
    return posPayload(p, cands);
  });
  const prompt = [
    'Ты помогаешь российскому поставщику понять, подходит ли его ассортимент под техническое задание тендера.',
    'Ниже позиции тендера с требованиями и кандидаты из прайса поставщика (у каждой позиции — список id кандидатов).',
    'Для КАЖДОЙ позиции выбери лучшего кандидата и оцени:',
    '- "подходит": товар точно проходит по всем требованиям;',
    '- "почти": не хватает данных или есть небольшие расхождения, которые надо проверить;',
    '- "нет": подходящего товара среди кандидатов нет.',
    'Опирайся на свои знания реальных характеристик моделей (процессор, память, порты, скорость печати и т. п.), если в прайсе их нет или их мало. Где не уверен, ставь "почти" и в "расхождения" напиши, что именно проверить. Ничего не выдумывай.',
    'Ответь СТРОГО JSON-массивом без пояснений, по одному объекту на позицию, в таком виде:',
    '[{"№":1,"статус":"подходит|почти|нет","товар":"наименование из прайса или пустая строка","расхождения":["коротко, чем отличается или что проверить"],"комментарий":"одна короткая фраза"}]',
    '',
    `Тендер: ${t.предмет}. Заказчик: ${t.заказчик || 'не указан'}. Закон: ${t.закон}. Коды ОКПД2: ${(t.окпд2 || []).join(', ') || 'нет'}.`,
    noTz ? 'ВАЖНО: технического задания у нас нет, есть только название тендера и коды ОКПД2. Позиции ниже — виды товара, выведенные из названия. Оценивай, подходит ли кандидат по виду и классу товара; "подходит" ставь только если название тендера и класс товара явно совпадают, иначе "почти" и напиши, что сверить в ТЗ.' : '',
    'ПОЗИЦИИ ТЕНДЕРА (JSON):',
    JSON.stringify(posList),
    'ПРАЙС ПОСТАВЩИКА, КАНДИДАТЫ (JSON):',
    JSON.stringify([...used.values()].map(itemPayload)),
  ].join('\n');
  return { prompt, used };
}

const STATUSES: Record<string, Status> = { 'подходит': 'подходит', 'почти': 'почти', 'нет': 'нет' };

/** Проверяем форму ответа: берём только то, что понимаем; недостающее добираем правилами */
export function parseAi(t: Tender, raw: unknown, catalog: Item[], used: Map<string, Item>): TenderResult {
  const rules = matchTender(t, catalog);
  if (!Array.isArray(raw)) throw new AiError('other', 'ИИ вернул ответ не того вида');
  const rows = new Map<number, AiRow>();
  for (const r of raw as AiRow[]) if (r && typeof r === 'object' && typeof r['№'] === 'number') rows.set(r['№'], r);
  let missing = 0;
  const positions: PosResult[] = rules.positions.map((rp) => {
    const r = rows.get(rp.no);
    const st = r && typeof r['статус'] === 'string' ? STATUSES[r['статус'].trim().toLowerCase()] : undefined;
    if (!r || !st) { missing++; return { ...rp, comment: rp.comment ? rp.comment + ' (правила)' : '(по правилам)' }; }
    const name = typeof r['товар'] === 'string' ? r['товар'].trim() : '';
    const item = name ? ([...used.values()].find((i) => i.name === name) || [...used.values()].find((i) => name.toLowerCase().includes(i.name.toLowerCase())) || ({ id: 'ai', name, brand: '', model: '', category: '', price: null, specs: {}, note: '' } as Item)) : null;
    const diffs = Array.isArray(r['расхождения']) ? (r['расхождения'] as unknown[]).filter((x): x is string => typeof x === 'string').slice(0, 4) : [];
    return {
      ...rp, status: st, item: st === 'нет' ? null : item,
      diffs: st === 'почти' ? diffs : [], check: st === 'подходит' ? diffs : [],
      comment: typeof r['комментарий'] === 'string' ? r['комментарий'].trim() : '',
    };
  });
  return summarize(t, positions, rules.noPositions, 'ИИ', missing ? `По ${missing} поз. ИИ не ответил, взяты правила.` : undefined);
}

export async function analyzeWithAi(t: Tender, catalog: Item[], signal?: AbortSignal): Promise<TenderResult> {
  const sample = await getSample();
  if (!sample) throw new AiError('not_granted', 'ИИ недоступен');
  const { prompt, used } = buildPrompt(t, catalog);
  let raw: unknown;
  try {
    raw = await sample.json<unknown>(prompt, { signal });
  } catch (e) {
    const code = (e as { code?: string })?.code;
    if (code === 'not_granted' || code === 'sampling_disabled' || code === 'not_declared' || code === 'capability_disabled' || code === 'capability_removed') throw new AiError('not_granted', 'нет согласия на ИИ');
    if (code === 'rate_limited') throw new AiError('rate_limited', 'много запросов');
    if (code === 'cancelled') throw new AiError('other', 'остановлено');
    throw new AiError('other', (e as { message?: string })?.message || 'ошибка ИИ');
  }
  return parseAi(t, raw, catalog, used);
}
