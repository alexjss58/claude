import { useEffect, useMemo, useRef, useState } from 'react';
import type { Need } from '../lib/search';
import { SUMS, searchTenders } from '../lib/search';
import { regionByCode, snapshot } from '../lib/data';
import { plural, rubShort } from '../lib/format';
import { Head, Check } from './ui';

export const MAX_PICK = 5;

export function searchKey(need: Need, regionCode: number | null): string {
  return JSON.stringify([need, regionCode]);
}

export function useRanked(need: Need, regionCode: number | null) {
  return useMemo(() => searchTenders(snapshot.тендеры, { need, regionCode }), [need, regionCode]);
}

const SCOPE_LABEL = { region: 'Мой регион', fo: 'Мой федеральный округ', all: 'Вся Россия' } as const;

export function Tenders({ need, regionCode, picked, searchDone, onDone, onPick, onNeed, onEdit }: {
  need: Need; regionCode: number | null; picked: string[] | null; searchDone: boolean;
  onDone: () => void; onPick: (ids: string[]) => void; onNeed: (n: Need) => void; onEdit: () => void;
}) {
  const ranked = useRanked(need, regionCode);
  const [busy, setBusy] = useState(!searchDone);
  const [phase, setPhase] = useState(0);
  const [shown, setShown] = useState(30);
  const doneRef = useRef(onDone);
  doneRef.current = onDone;

  useEffect(() => {
    if (searchDone) return;
    const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    const t1 = window.setTimeout(() => setPhase(1), reduce ? 0 : 450);
    const t2 = window.setTimeout(() => setPhase(2), reduce ? 0 : 900);
    const t3 = window.setTimeout(() => { setBusy(false); doneRef.current(); }, reduce ? 50 : 1400);
    return () => { window.clearTimeout(t1); window.clearTimeout(t2); window.clearTimeout(t3); };
  }, [searchDone]);

  // Первый показ: отмечаем 5 лучших
  const ids = ranked.map((r) => r.t.номер);
  useEffect(() => {
    if (busy) return;
    if (picked === null) onPick(ids.slice(0, MAX_PICK));
    else if (picked.some((p) => !ids.includes(p))) onPick(picked.filter((p) => ids.includes(p)));
  }, [busy, picked, ids.join('|')]); // eslint-disable-line react-hooks/exhaustive-deps

  const sel = picked || [];
  const toggle = (n: string) => {
    if (sel.includes(n)) onPick(sel.filter((x) => x !== n));
    else if (sel.length < MAX_PICK) onPick([...sel, n]);
  };

  const sumLabel = SUMS.find((s) => s.key === need.sum)?.label;
  const msgs = ['Читаем снимок ЕИС…', 'Отбираем по вашим условиям…', 'Ранжируем…'];

  if (busy) {
    return (
      <div className="searching" role="status" aria-live="polite">
        <p className="mono">{msgs[phase]}</p>
        <div className="pbar"><i /></div>
      </div>
    );
  }

  return (
    <div>
      <Head n="03" rubric="Тендеры" title="Тендеры" />
      <div className="sum-line">
        {need.niches.map((n) => <span className="tag" key={n}>{n}</span>)}
        {need.keywords.trim() ? <span className="tag">«{need.keywords.trim()}»</span> : null}
        <span className="tag">{SCOPE_LABEL[need.scope]}</span>
        <span className="tag">{sumLabel}</span>
        <button className="linkbtn" onClick={onEdit} style={{ padding: '0 4px', minHeight: 30 }}>Изменить</button>
      </div>

      {ranked.length === 0 ? (
        <div className="empty" role="status">
          <p style={{ fontSize: 22, fontWeight: 600 }}>Ничего не нашли</p>
          <p className="hint">Подача должна заканчиваться не раньше, чем через сутки; работы и услуги не показываем.</p>
          <div className="btnrow" style={{ marginTop: 16 }}>
            {need.scope !== 'all' ? <button className="btn" onClick={() => onNeed({ ...need, scope: 'all' })}>Расширить до всей России</button> : null}
            {need.sum !== 'any' ? <button className="btn" onClick={() => onNeed({ ...need, sum: 'any' })}>Убрать сумму</button> : null}
            <button className="btn" onClick={onEdit}>Изменить условия</button>
          </div>
        </div>
      ) : (
        <>
          <p className="found">Нашли <span className="num-hl">{ranked.length}</span>. Мы отметили {Math.min(MAX_PICK, ranked.length)} лучших для анализа</p>
          <p className="hint">Можно менять отметки: максимум {MAX_PICK}. Выбрано: {sel.length}.</p>
          <div className="cards" role="list">
            {ranked.slice(0, shown).map(({ t, days }) => {
              const on = sel.includes(t.номер);
              const full = !on && sel.length >= MAX_PICK;
              return (
                <article className="tcard" key={t.номер} role="listitem">
                  <button className="pick" aria-pressed={on} aria-label={`${on ? 'Снять отметку' : 'Отметить'}: ${t.предмет}`} disabled={full} onClick={() => toggle(t.номер)} style={full ? { opacity: 0.4 } : undefined}>
                    <Check on={on} />
                  </button>
                  <div className="body">
                    <h3>{t.предмет}</h3>
                    {t.заказчик ? <p className="cust">{t.заказчик}</p> : null}
                    <div className="tmeta">
                      <span className="big">{rubShort(t.нмц)}</span>
                      <span className="mono">{days === 0 ? 'меньше суток' : `осталось ${days} ${plural(days, 'день', 'дня', 'дней')}`}</span>
                    </div>
                    <div className="tmeta">
                      <span className="mono dim">{regionByCode(t.регион_код)?.название || t.регион || 'Регион не указан'}</span>
                      <span className="mono dim">{t.закон} · {t.способ.replace(/\s*\(извещение[^)]*\)/i, '')}</span>
                      <a className="mono tlink" href={t.ссылка} target="_blank" rel="noopener noreferrer">в ЕИС ↗</a>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
          {ranked.length > shown ? <div className="btnrow" style={{ marginTop: 18 }}><button className="btn" onClick={() => setShown(shown + 30)}>Показать ещё (осталось {ranked.length - shown})</button></div> : null}
        </>
      )}
    </div>
  );
}

