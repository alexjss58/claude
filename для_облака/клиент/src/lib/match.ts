// Сверка позиций тендера с ассортиментом ПРАВИЛАМИ (работает всегда, без ИИ).
// 1. Тип товара (ноутбук, МФУ, коммутатор…) определяем по названию позиции, затем по ОКПД2.
// 2. Кандидаты — товары того же типа; бренд и модель из позиции повышают очки.
// 3. Числовые условия (>=, <=, =, диапазон) проверяем по характеристикам товара, если они есть в прайсе.
//    Текстовые — ищем совпадение слов; не нашли — «проверьте».
// 4. Нет характеристик в прайсе — «≈ почти» и список того, что проверить.

import type { Item, PosResult, Position, Spec, Status, Tender, TenderResult } from '../types';

interface TypeDef { key: string; re: RegExp; okpd?: string[] }

// Порядок важен: первое совпадение выигрывает (специфичное — раньше общего).
export const TYPES: TypeDef[] = [
  { key: 'экран для проектора', re: /(экран[а-яё]*\s+(для\s+)?проектор|проекционн[а-яё]*\s+экран)/i },
  { key: 'мфу', re: /(мфу|многофункциональн[а-яё]*\s+(печатающ|устройств))/i, okpd: ['26.20.18'] },
  { key: 'принтер', re: /принтер/i, okpd: ['26.20.16.12'] },
  { key: 'сканер', re: /сканер/i, okpd: ['26.20.16.15'] },
  { key: 'клавиатура', re: /клавиатур/i, okpd: ['26.20.16.110'] },
  { key: 'мышь', re: /(мышь|манипулятор[а-яё]*\s+мышь)/i, okpd: ['26.20.16.170'] },
  { key: 'ноутбук', re: /(ноутбук|лэптоп|laptop)/i, okpd: ['26.20.11'] },
  { key: 'планшет', re: /планшет/i },
  { key: 'моноблок', re: /моноблок/i, okpd: ['26.20.15.140'] },
  { key: 'монитор', re: /монитор/i, okpd: ['26.20.17.110'] },
  { key: 'сервер', re: /сервер/i, okpd: ['26.20.14'] },
  { key: 'системный блок', re: /(системн[а-яё]*\s+блок|рабоч[а-яё]*\s+станц|настольн[а-яё]*\s+компьютер|персональн[а-яё]*\s+компьютер|автоматизированн[а-яё]*\s+рабоч|неттоп|^\s*компьютер(?!н))/i, okpd: ['26.20.15'] },
  { key: 'проектор', re: /проектор/i, okpd: ['26.20.17.120', '26.70.16'] },
  { key: 'ибп', re: /(ибп|бесперебойн|\bups\b)/i, okpd: ['26.20.40.11'] },
  { key: 'коммутатор', re: /(коммутатор|\bswitch\b)/i, okpd: ['26.30.11.11'] },
  { key: 'маршрутизатор', re: /(маршрутизатор|роутер|межсетевой)/i, okpd: ['26.30.11.12'] },
  { key: 'трансивер', re: /(трансивер|\bsfp\b|модул[а-яё]*\s+sfp)/i },
  { key: 'телефон', re: /(телефон|\bsip\b|\bdect\b)/i, okpd: ['26.30.23.17'] },
  { key: 'гарнитура', re: /(гарнитур|наушник)/i, okpd: ['26.40.42'] },
  { key: 'микшер', re: /микшер/i },
  { key: 'микрофон', re: /(микрофон|радиосистем)/i },
  { key: 'акустика', re: /(акустическ|колонк|громкоговорител|саундбар)/i },
  { key: 'веб-камера', re: /веб-?камер/i },
  { key: 'камера видеонаблюдения', re: /(камер[а-яё]*\s+видеонаблюд|ip-?камер)/i, okpd: ['26.70.13'] },
  { key: 'телевизор', re: /(телевизор|интерактивн[а-яё]*\s+панел|светодиодн[а-яё]*\s+дисплей)/i },
];

export function typeOfText(text: string): string | null {
  for (const t of TYPES) if (t.re.test(text)) return t.key;
  return null;
}

function typeOfPosition(p: Position): string | null {
  const byName = typeOfText(p.наименование);
  if (byName) return byName;
  for (const t of TYPES) if (t.okpd?.some((c) => (p.окпд2 || '').startsWith(c))) return t.key;
  return null;
}

export function typeOfItem(it: Item): string | null {
  return typeOfText(it.category) || typeOfText(it.name) || typeOfText(it.model);
}

/** Все типы товаров, названные в тексте (для тендеров без позиций) */
export function typesInText(text: string): string[] {
  return TYPES.filter((t) => t.re.test(text)).map((t) => t.key);
}

// ---------- слова и числа ----------
const STOP = new Set(['и', 'в', 'на', 'для', 'с', 'по', 'от', 'до', 'или', 'не', 'при', 'из', 'к', 'о', 'об', 'а', 'как', 'что', 'вид', 'шт',
  'макси', 'мини', 'колич', 'налич', 'возмо', 'режим', 'номин', 'значе', 'число', 'подде', 'форма', 'устро', 'допус', 'суммар', 'встро']);
const LOOK: Record<string, string> = { 'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'х': 'x', 'в': 'b', 'к': 'k', 'м': 'm', 'н': 'h', 'т': 't' };
function stems(s: string): string[] {
  const words = s.toLowerCase().replace(/ё/g, 'е').match(/[a-zа-я0-9]+/g) || [];
  const out: string[] = [];
  for (let w of words) {
    if (/\d/.test(w) && /[a-zа-я]/.test(w)) w = w.replace(/[а-я]/g, (c) => LOOK[c] || c); // «А4» кириллицей = «A4» латиницей
    const k = w.slice(0, 5);
    if (w.length < 2 || STOP.has(k) || STOP.has(w)) continue;
    out.push(k);
  }
  return out;
}

function toNum(s: string): number | null {
  const m = /-?\d+(?:[.,]\d+)?/.exec(s.replace(/\s(?=\d{3}\b)/g, ''));
  if (!m) return null;
  const n = Number(m[0].replace(',', '.'));
  return Number.isFinite(n) ? n : null;
}

const UNIT_FACTORS: Record<string, [string, number]> = {
  'тб': ['гб', 1000], 'тбайт': ['гб', 1000], 'гб': ['гб', 1], 'гбайт': ['гб', 1], 'мб': ['гб', 0.001], 'мбайт': ['гб', 0.001],
  'ггц': ['ггц', 1], 'мгц': ['ггц', 0.001], 'квт': ['вт', 1000], 'вт': ['вт', 1], 'ква': ['ва', 1000], 'ва': ['ва', 1],
  'гбит/с': ['гбит/с', 1], 'мбит/с': ['гбит/с', 0.001],
};
function unitNorm(u: string): [string, number] {
  const k = u.toLowerCase().replace(/[.\s]/g, '').replace('ё', 'е');
  return UNIT_FACTORS[k] || [k, 1];
}

/** Значение характеристики товара в единицах требования */
function itemNumber(value: string, headerUnit: string, reqUnit: string): number | null {
  // число должно стоять в начале, дальше — максимум одна единица («16», «1000.0», «3 шт»); «DDR4» или «10/100/1000BASE-T» числом не считаем
  if (!/^\s*-?\d+(?:[.,]\d+)?\s*[а-яёa-z°%²·/]{0,10}\.?\s*$/i.test(value)) return null;
  const n = toNum(value);
  if (n === null) return null;
  const inText = /(тб|тбайт|гб|гбайт|мб|мбайт|ггц|мгц|квт|вт|ква|ва|гбит\/с|мбит\/с)\b/i.exec(value.replace(/\d/g, ' '));
  const have = unitNorm(inText ? inText[1] : headerUnit);
  const want = unitNorm(reqUnit);
  if (!reqUnit || !have[0] || have[0] !== want[0]) return n;
  return (n * have[1]) / want[1];
}

function splitHeader(h: string): { name: string; unit: string } {
  const i = h.lastIndexOf(',');
  if (i < 0) return { name: h, unit: '' };
  return { name: h.slice(0, i), unit: h.slice(i + 1).trim() };
}

interface SpecKey { key: string; name: string; unit: string; set: Set<string> }
const keyCache = new WeakMap<Item, SpecKey[]>();
function keysOf(it: Item): SpecKey[] {
  let k = keyCache.get(it);
  if (!k) {
    k = Object.keys(it.specs).map((key) => { const { name, unit } = splitHeader(key); return { key, name, unit, set: new Set(stems(name)) }; });
    keyCache.set(it, k);
  }
  return k;
}

const GUARDS = [['верси'], ['цветн'], ['черно', 'белой', 'моноx'], ['вертик'], ['гориз']];
function guardOk(req: Set<string>, key: Set<string>): boolean {
  for (const g of GUARDS) {
    const r = g.some((x) => req.has(x)), k = g.some((x) => key.has(x));
    if (r !== k) return false;
  }
  return true;
}

function findSpec(it: Item, reqName: string): SpecKey | null {
  const rs = new Set(stems(splitHeader(reqName).name));
  if (!rs.size) return null;
  let best: SpecKey | null = null, bestScore = 0;
  for (const k of keysOf(it)) {
    if (!k.set.size) continue;
    let hit = 0;
    for (const w of k.set) if (rs.has(w)) hit++;
    if (!hit) continue;
    const covKey = hit / k.set.size, covReq = hit / rs.size;
    // колонка прайса — «голова» требования (все её слова есть в требовании) или требование почти целиком покрыто колонкой
    const accept = (covKey === 1 && (hit >= 2 || k.set.size === 1)) || covReq >= 0.7;
    if (!accept || !guardOk(rs, k.set)) continue;
    const score = covKey + covReq + hit * 0.05;
    if (score > bestScore) { best = k; bestScore = score; }
  }
  return best;
}

export type SpecVerdict = { kind: 'ok' | 'bad' | 'unknown'; text: string };

const short = (x: string, n = 70) => (x.length > n ? x.slice(0, n - 1) + '…' : x);
function fmtReq(s: Spec): string {
  const op = s.условие === '>=' ? '≥' : s.условие === '<=' ? '≤' : s.условие === 'диапазон' ? '' : s.условие === 'из_списка' ? '' : '';
  return short(`${splitHeader(s.имя).name} ${op}${op ? ' ' : ''}${s.значение}${s.единица ? ' ' + s.единица : ''}`.replace(/\s+/g, ' ').trim());
}

export function evalSpec(s: Spec, it: Item): SpecVerdict {
  const sk = findSpec(it, s.имя);
  if (!sk) return { kind: 'unknown', text: fmtReq(s) };
  const have = it.specs[sk.key];
  const unit = s.единица || splitHeader(s.имя).unit;
  // единицы не совпадают (дюйм и шт): это другая характеристика
  if (s.единица && sk.unit && unitNorm(s.единица)[0] !== unitNorm(sk.unit)[0]) return { kind: 'unknown', text: fmtReq(s) };
  const cond = s.условие;
  const haveText = `${have}${sk.unit && !/[a-zа-я]/i.test(have) ? ' ' + sk.unit : ''}`;
  if (cond === '>=' || cond === '<=' || (cond === '=' && toNum(s.значение) !== null && /^[\d\s.,]+$/.test(s.значение.trim()))) {
    const need = toNum(s.значение), val = itemNumber(have, sk.unit, unit);
    if (need === null || val === null) return { kind: 'unknown', text: fmtReq(s) };
    const ok = cond === '>=' ? val >= need : cond === '<=' ? val <= need : Math.abs(val - need) < 1e-9;
    return ok ? { kind: 'ok', text: '' } : { kind: 'bad', text: `${fmtReq(s)}, в прайсе ${haveText}` };
  }
  if (cond === 'диапазон') {
    const m = /(-?\d+(?:[.,]\d+)?)\s*[–—-]\s*(-?\d+(?:[.,]\d+)?)/.exec(s.значение);
    const val = itemNumber(have, sk.unit, unit);
    if (!m || val === null) return { kind: 'unknown', text: fmtReq(s) };
    const lo = Number(m[1].replace(',', '.')), hi = Number(m[2].replace(',', '.'));
    return val >= lo && val <= hi ? { kind: 'ok', text: '' } : { kind: 'bad', text: `${fmtReq(s)}, в прайсе ${haveText}` };
  }
  // текстовые условия: все слова требования есть в значении товара (для списка — хотя бы одно из вариантов)
  const hay = new Set(stems(have + ' ' + it.name));
  const parts = cond === 'из_списка' ? s.значение.split(/[;,]/) : [s.значение];
  const okText = parts.some((part) => { const w = stems(part); return w.length > 0 && w.every((x) => hay.has(x)); });
  if (okText) return { kind: 'ok', text: '' };
  if (/^(да|есть)$/i.test(s.значение.trim()) && /^(нет|0)/i.test(have.trim())) return { kind: 'bad', text: `${fmtReq(s)}, в прайсе: нет` };
  return { kind: 'unknown', text: `${fmtReq(s)} (в прайсе: ${have.slice(0, 40)})` };
}

// ---------- кандидаты ----------
interface Cand { item: Item; hard: string[]; soft: string[]; ok: number; noSpecs: boolean; score: number; numTotal: number; numOk: number; numUnknown: number }

function isNumeric(s: Spec): boolean {
  return s.условие === '>=' || s.условие === '<=' || s.условие === 'диапазон' || (s.условие === '=' && /^[\d\s.,]+$/.test(s.значение.trim()));
}

const BRANDS = /(hp|hewlett|canon|kyocera|xerox|brother|ricoh|epson|samsung|dell|lenovo|asus|acer|cisco|huawei|mikrotik|d-link|tp-link|eaton|apc|ippon|panasonic|yealink|fanvil|grandstream|logitech|jabra|shure|sennheiser|yamaha|aquarius|kraftway|iru|dexp|philips|lg|sony|viewsonic|benq|digma|zyxel|juniper|aruba|qtech|snom|cyberpower|powercom|crown|behringer)/i;

function brandTokens(text: string): string[] {
  return (text.toLowerCase().match(/[a-z][a-z0-9-]{1,}/g) || []).filter((w) => BRANDS.test(w) || /\d/.test(w));
}

function evaluate(p: Position, it: Item, brandWords: string[]): Cand {
  const hard: string[] = [], soft: string[] = [];
  let ok = 0, numTotal = 0, numOk = 0, numUnknown = 0;
  const hasSpecs = Object.keys(it.specs).length > 0;
  if (hasSpecs) {
    for (const s of p.характеристики) {
      const v = evalSpec(s, it);
      const num = isNumeric(s);
      if (num) numTotal++;
      if (v.kind === 'ok') { ok++; if (num) numOk++; }
      else if (v.kind === 'bad') hard.push(v.text);
      else { soft.push(v.text); if (num) numUnknown++; }
    }
    // числовые «не видно» важнее текстовых: их показываем первыми
    soft.sort((a, b) => Number(/[≥≤]/.test(b)) - Number(/[≥≤]/.test(a)));
  }
  const hay = (it.name + ' ' + it.brand + ' ' + it.model).toLowerCase();
  const brandHit = brandWords.filter((w) => hay.includes(w)).length;
  const score = brandHit * 3 + ok - hard.length * 4 - soft.length * 0.3 - (hasSpecs ? 0 : 5);
  return { item: it, hard, soft, ok, noSpecs: !hasSpecs, score, numTotal, numOk, numUnknown };
}

/** Кандидаты из ассортимента для позиции: тот же тип товара, иначе — по общим словам */
export function candidatesFor(p: Position, catalog: Item[], max = 10): Item[] {
  const ty = typeOfPosition(p);
  const words = brandTokens(p.наименование + ' ' + p.характеристики.map((c) => c.значение).join(' '));
  let list = ty ? catalog.filter((it) => typeOfItem(it) === ty) : [];
  if (!list.length && !ty) {
    const ps = new Set(stems(p.наименование));
    list = catalog.filter((it) => stems(it.name).some((w) => ps.has(w)));
  }
  return list.map((it) => evaluate(p, it, words)).sort((a, b) => b.score - a.score).slice(0, max).map((c) => c.item);
}

function checkList(p: Position): string[] {
  const num = p.характеристики.filter((s) => s.условие === '>=' || s.условие === '<=' || s.условие === 'диапазон');
  const src = num.length ? num : p.характеристики;
  return src.slice(0, 3).map(fmtReq);
}

export function matchPosition(p: Position, catalog: Item[]): PosResult {
  const base = { no: p['№'], name: p.наименование, qty: p.количество, unit: p.единица };
  const ty = typeOfPosition(p);
  const words = brandTokens(p.наименование + ' ' + p.характеристики.map((c) => c.значение).join(' '));
  let pool = ty ? catalog.filter((it) => typeOfItem(it) === ty) : [];
  if (!pool.length && !ty) {
    const ps = new Set(stems(p.наименование));
    pool = catalog.filter((it) => stems(it.name).some((w) => ps.has(w)));
  }
  if (!pool.length) return { ...base, status: 'нет', item: null, diffs: [], check: [], comment: '' };
  const best = pool.map((it) => evaluate(p, it, words)).sort((a, b) => b.score - a.score)[0];
  if (best.noSpecs) {
    return { ...base, status: 'почти', item: best.item, diffs: [], check: checkList(p), comment: 'в прайсе нет характеристик — проверьте' };
  }
  const total = p.характеристики.length;
  if (best.hard.length === 0) {
    const soft = best.soft.length;
    const numOkEnough = best.numOk >= 1 && best.numUnknown <= Math.max(1, Math.floor(best.numTotal * 0.15));
    if (soft === 0 || (numOkEnough && soft / Math.max(1, total) <= 0.7)) {
      return { ...base, status: 'подходит', item: best.item, diffs: [], check: best.soft.slice(0, 2), comment: '' };
    }
    return { ...base, status: 'почти', item: best.item, diffs: [], check: best.soft.slice(0, 2), comment: '' };
  }
  if (best.hard.length <= 2) {
    return { ...base, status: 'почти', item: best.item, diffs: best.hard, check: best.soft.slice(0, 2), comment: '' };
  }
  return { ...base, status: 'нет', item: null, diffs: [], check: [], comment: `ближайший товар не проходит по ${best.hard.length} условиям: например, ${best.hard[0]}` };
}

const label = (k: string) => (k.length <= 4 ? k.toUpperCase() : k[0].toUpperCase() + k.slice(1));

/** Тендер без структурных позиций (ТЗ в документах): «позиции» по видам товара из названия и кодов ОКПД2 */
export function pseudoPositions(t: Tender): Position[] {
  const keys = typesInText(t.предмет);
  const codeOf: Record<string, string> = {};
  for (const code of t.окпд2 || []) {
    for (const ty of TYPES) if (ty.okpd?.some((c) => code.startsWith(c))) { if (!keys.includes(ty.key)) keys.push(ty.key); codeOf[ty.key] = codeOf[ty.key] || code; }
  }
  if (!keys.length) return [{ '№': 1, наименование: t.предмет, окпд2: (t.окпд2 || [])[0] || '', количество: 1, единица: '', цена_за_ед: null, характеристики: [] }];
  return keys.slice(0, 6).map((k, i) => ({ '№': i + 1, наименование: label(k), окпд2: codeOf[k] || '', количество: 1, единица: '', цена_за_ед: null, характеристики: [] }));
}

export function matchTender(t: Tender, catalog: Item[]): TenderResult {
  if (t.позиции && t.позиции.length) {
    return summarize(t, t.позиции.map((p) => matchPosition(p, catalog)), false);
  }
  // Нет структурных позиций: сверяем по названию предмета, точнее — после загрузки ТЗ
  const words = brandTokens(t.предмет);
  const positions: PosResult[] = pseudoPositions(t).map((p) => {
    const base = { no: p['№'], name: p.наименование, qty: 0, unit: '' };
    const ty = typeOfPosition(p);
    let pool = ty ? catalog.filter((it) => typeOfItem(it) === ty) : [];
    if (!pool.length && !ty) { const ps = new Set(stems(p.наименование)); pool = catalog.filter((it) => stems(it.name).some((w) => ps.has(w))); }
    if (!pool.length) return { ...base, status: 'нет' as Status, item: null, diffs: [], check: [], comment: '' };
    const best = pool.map((it) => evaluate(p, it, words)).sort((a, b) => b.score - a.score)[0];
    return { ...base, status: 'почти' as Status, item: best.item, diffs: [], check: [], comment: `в ассортименте подходящего типа: ${pool.length} шт.; по названию, характеристики сверьте с ТЗ` };
  });
  return summarize(t, positions, true);
}

export function summarize(t: Tender, positions: PosResult[], noPositions: boolean, mode: 'правила' | 'ИИ' = 'правила', aiNote?: string): TenderResult {
  return {
    number: t.номер, mode, noPositions, positions,
    closed: positions.filter((p) => p.status === 'подходит').length,
    almost: positions.filter((p) => p.status === 'почти').length,
    total: positions.length, aiNote,
  };
}

export type { Status };
