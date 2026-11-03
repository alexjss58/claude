import type { Tender } from '../types';
import { daysLeft } from './search';
import { natInfo, type NatInfo } from './natreg';

const BRAND_RE = /(?<![A-Za-z])(hp|hewlett[- ]packard|canon|kyocera|xerox|brother|ricoh|epson|samsung|dell|lenovo|asus|acer|cisco|huawei|mikrotik|d-link|tp-link|eaton|apc|ippon|panasonic|yealink|fanvil|grandstream|logitech|jabra|shure|sennheiser|yamaha|aquarius|kraftway|iru|dexp|philips|lg|sony|viewsonic|benq|digma|zyxel|juniper|aruba|qtech)(?![A-Za-z])/i;
const MODEL_RE = /\b[A-Z]{1,5}[- ]?[A-Z]*\d{2,}[A-Z0-9-]*\b/; // KX-TDE600RU, ProBook 450 → «KX-TDE600RU»
const EQUIV_RE = /эквивалент|аналог/i;

export function risksOf(t: Tender, now = Date.now()): string[] {
  const r: string[] = [];
  const d = daysLeft(t, now);
  if (d < 3) r.push(`До окончания подачи ${d <= 1 ? 'около суток' : d + ' дн.'}: на документы и подпись времени мало.`);
  const named = t.флаги.includes('бренд в названии') || BRAND_RE.test(t.предмет) || MODEL_RE.test(t.предмет);
  if (named && !EQUIV_RE.test(t.предмет)) r.push('В предмете есть бренд или модель, слов «или эквивалент» не видно: уточните в документации.');
  const c = t.обеспечение_контракта_проц;
  if (typeof c === 'number' && c > 10) r.push(`Обеспечение контракта ${c.toLocaleString('ru-RU')}%: больше 10%, замораживаются большие деньги.`);
  return r;
}

const ORDER: Record<NatInfo['mode'], number> = { запрет: 3, ограничение: 2, преимущество: 1, неизвестно: 0 };

export interface NatLine { info: NatInfo; code: string; extra: number }

/** Самая строгая мера по кодам ОКПД2 тендера (по позициям, иначе по списку кодов тендера) */
export function natOf(t: Tender): NatLine | null {
  const codes = Array.from(new Set((t.позиции && t.позиции.length ? t.позиции.map((p) => p.окпд2) : t.окпд2).filter(Boolean)));
  if (!codes.length) return null;
  let best: NatLine | null = null;
  for (const c of codes) {
    const info = natInfo(c);
    if (!best || ORDER[info.mode] > ORDER[best.info.mode]) best = { info, code: c, extra: codes.length - 1 };
  }
  return best;
}
