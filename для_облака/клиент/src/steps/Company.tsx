import { useMemo, useState } from 'react';
import type { Company as C } from '../state';
import { regions } from '../lib/data';
import { Head } from './ui';

export function innError(inn: string): string {
  const v = inn.replace(/\s/g, '');
  if (!v) return '';
  if (!/^\d+$/.test(v)) return 'ИНН — только цифры';
  if (v.length !== 10 && v.length !== 12) return 'В ИНН 10 цифр (организация) или 12 (ИП)';
  return '';
}

export function Company({ value, onChange, showErrors }: { value: C; onChange: (c: C) => void; showErrors: boolean }) {
  const [q, setQ] = useState('');
  const [open, setOpen] = useState(false);
  const cur = regions.find((r) => r.код === value.regionCode);
  const list = useMemo(() => {
    const s = q.trim().toLowerCase().replace(/ё/g, 'е');
    return (s ? regions.filter((r) => r.название.toLowerCase().replace(/ё/g, 'е').includes(s)) : regions).slice(0, 40);
  }, [q]);
  const ie = innError(value.inn);

  return (
    <div className="stack">
      <Head n="01" rubric="О компании" title="О компании" />
      <label className="field">
        <span className="lbl mono">Название</span>
        <input className="input" value={value.name} autoComplete="organization" placeholder="ООО «Ромашка»"
          aria-invalid={showErrors && !value.name.trim()} onChange={(e) => onChange({ ...value, name: e.target.value })} />
        {showErrors && !value.name.trim() ? <p className="err">Напишите название компании</p> : null}
      </label>
      <label className="field">
        <span className="lbl mono">ИНН (необязательно)</span>
        <input className="input" value={value.inn} inputMode="numeric" autoComplete="off" placeholder="10 или 12 цифр"
          aria-invalid={!!ie && (showErrors || value.inn.length > 0)} aria-describedby="inn-e"
          onChange={(e) => onChange({ ...value, inn: e.target.value.replace(/[^\d\s]/g, '').slice(0, 14) })} />
        <span id="inn-e">{ie && (showErrors || value.inn.replace(/\s/g, '').length >= 10) ? <span className="err">{ie}</span> : null}</span>
      </label>
      <div className="field" role="group" aria-label="Регион">
        <span className="lbl mono">Регион</span>
        <input className="input" value={open ? q : cur?.название || ''} placeholder="Начните вводить: Москва, Татарстан…"
          role="combobox" aria-expanded={open} aria-controls="reg-list" aria-autocomplete="list" autoComplete="off"
          onFocus={() => { setOpen(true); setQ(''); }}
          onChange={(e) => { setQ(e.target.value); setOpen(true); }} />
        {open ? (
          <ul id="reg-list" role="listbox" className="dd">
            {list.length === 0 ? <li className="hint" style={{ padding: 12 }}>Не нашли такой регион</li> : null}
            {list.map((r) => (
              <li key={r.код} role="option" aria-selected={r.код === value.regionCode}>
                <button type="button"
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => { onChange({ ...value, regionCode: r.код }); setOpen(false); setQ(''); }}
                  aria-pressed={r.код === value.regionCode}>{r.название} <span className="mono dim">{r.фо}</span></button>
              </li>
            ))}
          </ul>
        ) : null}
        {open ? <button type="button" className="linkbtn" onClick={() => setOpen(false)}>Закрыть список</button> : null}
      </div>
      <fieldset className="field">
        <legend className="lbl mono">Есть электронная подпись?</legend>
        <div className="seg three" role="radiogroup" aria-label="Есть электронная подпись?">
          {(['да', 'нет', 'не знаю'] as const).map((o) => (
            <button key={o} type="button" role="radio" aria-checked={value.eds === o} onClick={() => onChange({ ...value, eds: o })}>{o[0].toUpperCase() + o.slice(1)}</button>
          ))}
        </div>
      </fieldset>
      <p className="mono dim">Данные остаются в вашем браузере</p>
    </div>
  );
}
