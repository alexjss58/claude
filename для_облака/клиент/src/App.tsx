import { useCallback, useEffect, useMemo, useState } from 'react';
import { useAppState } from './state';
import { Start } from './steps/Start';
import { Company, innError } from './steps/Company';
import { Need } from './steps/Need';
import { MAX_PICK, Tenders, searchKey, useRanked } from './steps/Tenders';
import { Assortment } from './steps/Assortment';
import { Analysis } from './steps/Analysis';
import { Price, calcFor } from './steps/Price';
import { tenderByNumber } from './lib/data';
import { matchTender } from './lib/match';
import type { Tender, TenderResult } from './types';
import { getDownloads } from './lib/save';

const LABELS = ['Компания', 'Запрос', 'Тендеры', 'Ассортимент', 'Анализ', 'Цена'];

export function App() {
  const { state, patch, reset } = useAppState();
  const { step, company, need, picked, catalog, ai } = state;
  const [showErrors, setShowErrors] = useState(false);
  const [confirmReset, setConfirmReset] = useState(false);
  useEffect(() => { void getDownloads(); }, []); // заранее узнаём, доступно ли сохранение файлов на claude.ai

  const key = searchKey(need, company.regionCode);
  const ranked = useRanked(need, company.regionCode);
  const pickedTenders = useMemo(
    () => (picked || []).map((n) => tenderByNumber(n)).filter((t): t is Tender => !!t).slice(0, MAX_PICK),
    [picked],
  );
  const rules = useMemo(() => {
    const out: Record<string, TenderResult> = {};
    if (step >= 5) for (const t of pickedTenders) out[t.номер] = matchTender(t, catalog.items);
    return out;
  }, [step, pickedTenders, catalog.items]);
  const results = useMemo(() => {
    const out: Record<string, TenderResult> = {};
    for (const t of pickedTenders) if (rules[t.номер] || ai[t.номер]) out[t.номер] = ai[t.номер] || rules[t.номер];
    return out;
  }, [pickedTenders, rules, ai]);

  const go = useCallback((n: number) => { patch({ step: n }); setShowErrors(false); setConfirmReset(false); }, [patch]);
  useEffect(() => { window.scrollTo(0, 0); }, [step]);

  // Что мешает идти дальше
  let blocker = '';
  if (step === 1) {
    if (!company.name.trim()) blocker = 'Напишите название компании';
    else if (innError(company.inn)) blocker = innError(company.inn);
  } else if (step === 2) {
    if (!need.niches.length && !need.keywords.trim()) blocker = 'Выберите, чем торгуете, или впишите ключевые слова';
  } else if (step === 3) {
    if (key !== state.searchKey) blocker = '';
    else if (!(picked || []).length) blocker = ranked.length ? 'Отметьте хотя бы один тендер' : 'Расширьте условия поиска';
  } else if (step === 4) {
    if (!catalog.items.length) blocker = 'Загрузите прайс, вставьте список или выберите пример';
  }

  const next = () => {
    if (blocker) { setShowErrors(true); return; }
    if (step === 2) { patch({ step: 3, picked: key === state.searchKey ? picked : null }); setShowErrors(false); return; }
    if (step === 3 && key !== state.searchKey) return;
    if (step === 6) { document.getElementById('apply')?.scrollIntoView({ behavior: 'smooth', block: 'center' }); return; }
    go(step + 1);
  };

  const calcs = useMemo(
    () => (step === 6 ? pickedTenders.filter((t) => results[t.номер]).map((t) => calcFor(t, results[t.номер], state.participants, state.costs)) : []),
    [step, pickedTenders, results, state.participants, state.costs],
  );

  if (step === 0) {
    return <div className="page"><div className="frame">
      <header className="mast"><span className="brand"><span className="mono-mark" aria-hidden="true">ТК</span><span className="mono">Тендер под ключ</span></span></header>
      <Start onStart={() => go(1)} />
    </div></div>;
  }

  const nextLabel = ['', 'Дальше', 'Найти тендеры', 'К ассортименту', 'К анализу', 'К цене', 'Хочу подать с вами'][step];

  return (
    <div className="page"><div className="frame">
      <header className="mast">
        <button className="brand linkbtn" style={{ textDecoration: 'none', padding: 0, minHeight: 44 }} onClick={() => go(0)} aria-label="На стартовый экран">
          <span className="mono-mark" aria-hidden="true">ТК</span><span className="mono">Тендер под ключ</span>
        </button>
        {confirmReset ? (
          <span className="btnrow" style={{ alignItems: 'center', gap: 4 }}>
            <span className="mono">Стереть всё?</span>
            <button className="linkbtn" onClick={() => { reset(); setConfirmReset(false); setShowErrors(false); }}>Да</button>
            <button className="linkbtn" onClick={() => setConfirmReset(false)}>Нет</button>
          </span>
        ) : <button className="linkbtn" onClick={() => setConfirmReset(true)}>Начать заново</button>}
      </header>
      <nav aria-label="Шаги">
        <ol className="steps">
          {LABELS.map((l, i) => {
            const n = i + 1;
            return (
              <li key={l}>
                <button className={'step-cell' + (n === step ? ' cur' : n < step ? ' done' : '')} disabled={n > step} aria-current={n === step ? 'step' : undefined} onClick={() => go(n)} aria-label={`Шаг ${n}: ${l}`}>
                  <span>{String(n).padStart(2, '0')}</span><span className="lbl">{l}</span>
                </button>
              </li>
            );
          })}
        </ol>
      </nav>

      <main className="wrap">
        {step === 1 ? <Company value={company} onChange={(c) => patch({ company: c })} showErrors={showErrors} /> : null}
        {step === 2 ? <Need value={need} onChange={(n) => patch({ need: n })} hasRegion={company.regionCode != null} /> : null}
        {step === 3 ? (
          <Tenders need={need} regionCode={company.regionCode} picked={picked} searchDone={key === state.searchKey}
            onDone={() => patch({ searchKey: key })} onPick={(ids) => patch({ picked: ids })}
            onNeed={(n) => patch({ need: n, picked: null, searchKey: '' })} onEdit={() => go(2)} />
        ) : null}
        {step === 4 ? <Assortment value={catalog} onChange={(c) => patch({ catalog: c, ai: {} })} /> : null}
        {step === 5 ? <Analysis tenders={pickedTenders} rules={rules} ai={ai} catalog={catalog.items} onAi={(r) => patch({ ai: r })} /> : null}
        {step === 6 ? (
          <Price calcs={calcs} company={company.name} participants={state.participants} costs={state.costs} contact={state.contact}
            onParts={(n, p) => patch((s) => ({ participants: { ...s.participants, [n]: p } }))}
            onCost={(n, v) => patch((s) => ({ costs: { ...s.costs, [n]: v } }))}
            onContact={(c) => patch({ contact: c })} />
        ) : null}
      </main>

      <div className="nav">
        {blocker && showErrors ? <p className="nav-hint" role="alert">{blocker}</p> : null}
        <div className="nav-in">
          <button className="btn" onClick={() => go(step - 1)}>Назад</button>
          {(step === 3 && key !== state.searchKey) || (step === 6 && state.contact.sent) ? null : (
            <button className="btn primary" onClick={next} aria-disabled={!!blocker} style={blocker ? { opacity: 0.55 } : undefined}>{nextLabel}</button>
          )}
        </div>
      </div>
    </div></div>
  );
}
