// Форматирование чисел, денег и дат по-русски.

const nf0 = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 });
const nf1 = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 1, minimumFractionDigits: 0 });

export function rub(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  return `${nf0.format(Math.round(v))} ₽`;
}

/** Коротко: 1,5 млн ₽ / 820 тыс. ₽ */
export function rubShort(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  const a = Math.abs(v);
  if (a >= 1e9) return `${nf1.format(v / 1e9)} млрд ₽`;
  if (a >= 1e6) return `${nf1.format(v / 1e6)} млн ₽`;
  if (a >= 1e3) return `${nf0.format(v / 1e3)} тыс. ₽`;
  return `${nf0.format(v)} ₽`;
}

export function num(v: number | null | undefined, digits = 0): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: digits }).format(v);
}

export function pct(v: number | null | undefined, digits = 1): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  return `${new Intl.NumberFormat('ru-RU', { maximumFractionDigits: digits }).format(v)}%`;
}

/** «30.10.2026» → Date */
export function parseRuDate(s: string | null | undefined): Date | null {
  if (!s) return null;
  const m = /^(\d{2})\.(\d{2})\.(\d{4})/.exec(s);
  if (!m) return null;
  return new Date(Number(m[3]), Number(m[2]) - 1, Number(m[1]));
}

const MONTHS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];
export function dateLong(d: Date): string {
  return `${d.getDate()} ${MONTHS[d.getMonth()]}`;
}
export function dateShort(d: Date): string {
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

/** Склонение: plural(5, 'закупка', 'закупки', 'закупок') */
export function plural(n: number, one: string, few: string, many: string): string {
  const n10 = n % 10, n100 = n % 100;
  if (n10 === 1 && n100 !== 11) return one;
  if (n10 >= 2 && n10 <= 4 && (n100 < 12 || n100 > 14)) return few;
  return many;
}

/** Число из строки прайса: «52 000», «52000,50», «52 000 ₽» */
export function parseNumber(v: unknown): number | null {
  if (v === null || v === undefined) return null;
  if (typeof v === 'number') return Number.isFinite(v) ? v : null;
  const s = String(v).replace(/\s| /g, '').replace(/[₽рруб.]+$/i, '').replace(',', '.');
  if (!s) return null;
  const n = Number(s.replace(/[^\d.-]/g, ''));
  return Number.isFinite(n) && /\d/.test(s) ? n : null;
}

/** Римские цифры для нумерации разделов (журнальный приём) */
export function roman(n: number): string {
  const map: [number, string][] = [[10, 'X'], [9, 'IX'], [5, 'V'], [4, 'IV'], [1, 'I']];
  let out = '';
  for (const [v, s] of map) while (n >= v) { out += s; n -= v; }
  return out;
}

/** «ГОСУДАРСТВЕННОЕ УЧРЕЖДЕНИЕ "ИМЯ"» -> «Государственное учреждение "Имя"»: ЕИС отдаёт названия заглавными буквами */
export function niceName(s: string): string {
  const letters = s.replace(/[^A-Za-zА-Яа-яЁё]/g, '');
  if (!letters || letters !== letters.toUpperCase()) return s.replace(/\s+/g, ' ').trim();
  const low = s.toLowerCase().replace(/\s+/g, ' ').trim();
  return low.replace(/(^|["«(]\s?)(\p{L})/gu, (_m, a: string, b: string) => a + b.toUpperCase());
}
