import type { Need as N } from '../lib/search';
import { SUMS } from '../lib/search';
import { NICHES } from '../lib/data';
import { Head, Check } from './ui';

export function Need({ value, onChange, hasRegion }: { value: N; onChange: (n: N) => void; hasRegion: boolean }) {
  const toggle = (n: string) => onChange({ ...value, niches: value.niches.includes(n) ? value.niches.filter((x) => x !== n) : [...value.niches, n] });
  return (
    <div className="stack">
      <Head n="02" rubric="Что ищете" title="Что ищете" />
      <div className="field" role="group" aria-label="Чем торгуете">
        <span className="lbl mono">Чем торгуете (можно несколько)</span>
        <div className="tiles">
          {NICHES.map((n, i) => (
            <button key={n} type="button" className="tile" aria-pressed={value.niches.includes(n)} onClick={() => toggle(n)}>
              <span className="mono">{String(i + 1).padStart(2, '0')}</span>
              <span>{n}</span>
              <Check on={value.niches.includes(n)} />
            </button>
          ))}
        </div>
      </div>
      <label className="field">
        <span className="lbl mono">Ключевые слова (необязательно)</span>
        <input className="input" value={value.keywords} placeholder="Например: МФУ, проекторы" autoComplete="off" enterKeyHint="done"
          onChange={(e) => onChange({ ...value, keywords: e.target.value })} />
      </label>
      <div className="field" role="radiogroup" aria-label="Где готовы поставлять">
        <span className="lbl mono">Где готовы поставлять</span>
        <div className="seg three">
          {([['region', 'Мой регион'], ['fo', 'Мой федеральный округ'], ['all', 'Вся Россия']] as const).map(([k, l]) => (
            <button key={k} type="button" role="radio" aria-checked={value.scope === k} onClick={() => onChange({ ...value, scope: k })}>{l}</button>
          ))}
        </div>
        {!hasRegion && value.scope !== 'all' ? <p className="hint">Регион не указан на первом шаге, поэтому ищем по всей России.</p> : null}
      </div>
      <div className="field" role="radiogroup" aria-label="Сумма контракта">
        <span className="lbl mono">Сумма контракта</span>
        <div className="seg four">
          {SUMS.map((s) => (
            <button key={s.key} type="button" role="radio" aria-checked={value.sum === s.key} onClick={() => onChange({ ...value, sum: s.key })}>{s.label}</button>
          ))}
        </div>
      </div>
    </div>
  );
}
