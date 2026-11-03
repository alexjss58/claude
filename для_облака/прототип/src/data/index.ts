// Все данные прототипа собираются здесь. Ничего не грузится по сети: JSON встраивается в сборку.
//
// Откуда что:
//  - tenders.json, market.json, price_table_own.json — scripts/prepare_data.py из выгрузок Тендерплана;
//  - sverka/*.json — наши демо-примеры сверки в формате блока G (scripts/make_demo_files.py);
//  - sverka_engine/*.json — файлы движка блока G (копирует scripts/sync_external.mjs перед сборкой);
//    если они есть, показываем их ВМЕСТО демо-примеров;
//  - price_table_h.json — таблица цены блока H (если есть), иначе своя оценка.

import type { MarketNiche, NicheCode, PriceRow, Sverka, Tender, TenderView } from '../types';
import tendersRaw from './tenders.json';
import marketRaw from './market.json';
import ownPrice from './price_table_own.json';
import sampleCsv from './sample_price.csv?raw';

const hPriceMod = import.meta.glob('./price_table_h.json', { eager: true, import: 'default' }) as Record<string, PriceRow[]>;
const demoMods = import.meta.glob('./sverka/*.json', { eager: true, import: 'default' }) as Record<string, Sverka>;
const engineMods = import.meta.glob('./sverka_engine/*.json', { eager: true, import: 'default' }) as Record<string, Sverka>;

export const SOURCE_NOTE = 'по данным Тендерплана, ноябрь 2026, оценка';

export const tendersMeta = (tendersRaw as unknown as { meta: Record<string, string | number> }).meta;
export const tenders: Tender[] = (tendersRaw as unknown as { закупки: Tender[] }).закупки;
export interface Leaders { код: NicheCode; поставщики: { место: number; участий: number; побед: number }[] }
export const market = marketRaw as unknown as { подпись: string; ниши: MarketNiche[]; лидеры?: Leaders[] };

const hPrice = Object.values(hPriceMod)[0];
export const priceTable: PriceRow[] = hPrice && hPrice.length ? hPrice : (ownPrice as PriceRow[]);
export const priceSource = hPrice && hPrice.length
  ? 'модуль цены (блок H): медианы по выгрузкам Тендерплана'
  : 'наша оценка по выгрузкам Тендерплана (scripts/prepare_data.py)';

const engine = Object.values(engineMods).filter((s) => s && s.закупка && Array.isArray(s.позиции));
export const sverkaFromEngine = engine.length > 0;
export const sverkaList: Sverka[] = sverkaFromEngine ? engine : Object.values(demoMods);
export const sverkaSource = sverkaFromEngine
  ? 'движок сверки (блок G), файлы из движок/демо_выход/'
  : 'демо, пример: сверка подготовлена вручную в формате движка (блок G)';

export const samplePriceCsv: string = sampleCsv;

export const NICHE_NAMES: Record<NicheCode, string> = {
  svyaz: 'Связь и аудио-видео',
  pribory: 'Приборы',
};

/** Ниша для закупки со сверкой — по словам в предмете и позициях */
function guessNiche(s: Sverka): NicheCode {
  const text = (s.закупка.предмет + ' ' + s.позиции.map((p) => p.наименование).join(' ')).toLowerCase();
  const pr = /(прибор|измерен|мультиметр|термо|гигро|тепловизор|анализатор|манометр|датчик|лаборатор)/.test(text);
  const sv = /(телефон|связ|аудио|видео|проектор|микрофон|акустич|радио|коммутатор|ноутбук|компьютер|монитор|мфу)/.test(text);
  return pr && !sv ? 'pribory' : pr && sv && /средств\w* измерен/.test(text) ? 'pribory' : 'svyaz';
}

export function sverkaKey(s: Sverka): string {
  return 's-' + (s.закупка.номер || s.закупка.предмет).replace(/[^\p{L}\p{N}-]+/gu, '_');
}

function viewFromTender(t: Tender): TenderView {
  return {
    key: t.id,
    kind: 'выгрузка',
    предмет: t.предмет,
    заказчик: t.заказчик,
    инн_заказчика: t.инн_заказчика,
    ниша: t.ниша,
    закон: t.закон,
    способ: t.способ,
    статус: t.статус,
    нмц: t.нмц,
    обеспечение_заявки: t.обеспечение_заявки,
    обеспечение_контракта: t.обеспечение_контракта,
    регион: t.регион || '—',
    дата_окончания: t.дата_окончания,
    'снижение_%': t['снижение_%'],
    участников: t.участников,
    цена_победителя: t.цена_победителя,
    история_заказчика: t.история_заказчика,
    бейджи: t.бейджи,
    риски: t.риски,
    источник: 'Тендерплан, завершённая закупка (выгрузка ноября 2026)',
  };
}

function viewFromSverka(s: Sverka): TenderView {
  const z = s.закупка;
  const method = /котиров/i.test(z.способ) ? 'Запрос котировок' : /аукцион/i.test(z.способ) ? 'Электронный аукцион'
    : /предложен/i.test(z.способ) ? 'Запрос предложений' : /конкурс/i.test(z.способ) ? 'Конкурс' : z.способ || 'Иной способ';
  const brandNoEquiv = s.позиции.some((p) => p.характеристики.some((c) => c.эквивалент_допускается === false));
  const risks: string[] = [];
  if (brandNoEquiv) risks.push('В техзадании есть требования без «или эквивалент» — проверить, не под конкретный товар ли.');
  if (s.итог.нет > 0) risks.push(`Не хватает товара по ${s.итог.нет} ${plural(s.итог.нет)}: нужен поставщик-партнёр или отказ от лота.`);
  if (/котиров/i.test(z.способ)) risks.push('Запрос котировок идёт быстро: на подачу обычно несколько дней.');
  return {
    key: sverkaKey(s),
    kind: 'сверка',
    номер: z.номер,
    предмет: z.предмет,
    заказчик: z.заказчик,
    инн_заказчика: z.инн_заказчика,
    ниша: guessNiche(s),
    закон: z.закон,
    способ: method,
    статус: 'Подача заявок (демо)',
    нмц: z.нмц || null,
    // В формате движка нет обеспечения — не выдумываем, в «Сроках и деньгах» его вводят вручную.
    обеспечение_заявки: null,
    обеспечение_контракта: null,
    регион: z.регион || '—',
    дата_окончания: z.дата_окончания,
    'снижение_%': null,
    участников: null,
    цена_победителя: null,
    история_заказчика: null,
    бейджи: [
      { код: 'natreg', текст: 'нацрежим', почему: 'группа товаров, где обычно действует нацрежим (ПП РФ № 1875) — проверить по извещению' },
      ...(brandNoEquiv ? [{ код: 'svoy' as const, текст: 'под своего?', почему: 'есть требования без «или эквивалент»' }] : []),
    ],
    риски: risks,
    sverka: s,
    источник: sverkaFromEngine ? 'движок сверки (блок G)' : 'демо, пример (позиции составлены для показа)',
  };
}

function plural(n: number) {
  return n % 10 === 1 && n % 100 !== 11 ? 'позиции' : 'позициям';
}

export const sverkaViews: TenderView[] = sverkaList.map(viewFromSverka);
export const tenderViews: TenderView[] = tenders.map(viewFromTender);
const byKey = new Map<string, TenderView>([...sverkaViews, ...tenderViews].map((v) => [v.key, v]));

export function getTenderView(key: string | undefined): TenderView | undefined {
  if (!key) return undefined;
  return byKey.get(key) || byKey.get(decodeURIComponent(key));
}

export const regions: string[] = (() => {
  const c = new Map<string, number>();
  for (const t of tenders) if (t.регион) c.set(t.регион, (c.get(t.регион) || 0) + 1);
  return [...c.entries()].sort((a, b) => b[1] - a[1]).map(([r]) => r);
})();

/** Первая закупка с готовой сверкой — на неё ведут ссылки «посмотреть в демо» */
export const firstSverkaKey: string = sverkaViews[0]?.key || tenderViews[0]?.key || '';
