import { useEffect, useRef, useState } from 'react';
import type { PosResult, Tender, TenderResult } from '../types';
import type { Item } from '../types';
import { AiError, analyzeWithAi, getSample } from '../lib/ai';
import { runtime } from '../lib/save';
import { MODE_TITLE, whatToDo } from '../lib/natreg';
import { natOf, risksOf } from '../lib/risks';
import { plural } from '../lib/format';
import { Head } from './ui';

const MARK = { 'подходит': ['ok', '✓', 'Подходит'], 'почти': ['almost', '≈', 'Почти'], 'нет': ['no', '✕', 'Нет в ассортименте'] } as const;

function Pos({ r, noPositions }: { r: PosResult; noPositions: boolean }) {
  const [cls, ch, word] = MARK[r.status];
  return (
    <li>
      <span className={'badge ' + cls} aria-hidden="true">{ch}</span>
      <div>
        <p className="pname"><span className="st">{word}</span>{r.name}{!noPositions && r.qty ? <span className="dim"> · {r.qty} {r.unit}</span> : null}</p>
        {r.item ? <p className="psub">Из ассортимента: {r.item.name}</p> : null}
        {r.diffs.length ? <p className="psub">Чем отличается: {r.diffs.join('; ')}</p> : null}
        {r.check.length ? <p className="psub">{r.status === 'почти' && r.comment.includes('нет характеристик') ? 'В прайсе нет характеристик — проверьте: ' : 'Проверьте: '}{r.check.join('; ')}</p> : null}
        {r.comment && !r.comment.includes('нет характеристик') ? <p className="psub">{r.comment}</p> : null}
      </div>
    </li>
  );
}

function TenderBlock({ t, res }: { t: Tender; res: TenderResult }) {
  const [all, setAll] = useState(false);
  const nat = natOf(t);
  const risks = risksOf(t);
  const shown = all ? res.positions : res.positions.slice(0, 6);
  return (
    <section className="tres" aria-label={t.предмет}>
      <div className="tres-h">
        <h3>{t.предмет}</h3>
        <p className="close-line">
          {res.noPositions
            ? <span>По названию подходит <span className="hl">{res.positions.filter((p) => p.status !== 'нет').length}</span> из {res.total} {plural(res.total, 'вида', 'видов', 'видов')} товара</span>
            : <span>Закрываете <span className="hl">{res.closed}</span> из {res.total} {plural(res.total, 'позиции', 'позиций', 'позиций')}</span>}
          {!res.noPositions && res.almost ? <span className="mono dim">ещё {res.almost} почти</span> : null}
        </p>
        {res.noPositions ? <p className="hint">ТЗ в документах — сверка по названию, точнее после загрузки ТЗ.</p> : null}
        {res.mode === 'ИИ' ? <p className="mono dim" style={{ marginTop: 6 }}>Сверка: ИИ (Claude)</p> : null}
        {res.aiNote ? <p className="hint">{res.aiNote}</p> : null}
      </div>
      <ul className="pos">{shown.map((r) => <Pos key={r.no} r={r} noPositions={res.noPositions} />)}</ul>
      {res.positions.length > 6 ? <button className="linkbtn more" onClick={() => setAll(!all)}>{all ? 'Свернуть' : `Показать все ${res.positions.length}`}</button> : null}
      <div className="tres-row">
        <span className="mono">Нацрежим</span>
        {nat ? (
          <p><strong>{MODE_TITLE[nat.info.mode]}</strong>{nat.info.rule ? <> — {nat.info.rule.что} ({nat.info.rule.где}){nat.extra > 0 ? `, ещё ${nat.extra} ${plural(nat.extra, 'код', 'кода', 'кодов')}` : ''}</> : null}. {' '}{whatToDo(nat.info, t.закон).split('. ').slice(0, 2).join('. ').replace(/\.?$/, '.')}</p>
        ) : <p>Код ОКПД2 не указан: меру смотрите в извещении.</p>}
      </div>
      <div className="tres-row">
        <span className="mono">Риски</span>
        {risks.length ? <ul>{risks.map((x) => <li key={x}>{x}</li>)}</ul> : <p>Явных рисков по данным снимка не видно.</p>}
      </div>
    </section>
  );
}

export function Analysis({ tenders, rules, ai, catalog, onAi }: {
  tenders: Tender[]; rules: Record<string, TenderResult>; ai: Record<string, TenderResult>; catalog: Item[];
  onAi: (res: Record<string, TenderResult>) => void;
}) {
  const [can, setCan] = useState<boolean | null>(() => (runtime() ? null : false));
  const [waited, setWaited] = useState(false);
  const [busy, setBusy] = useState<string>('');
  const [msg, setMsg] = useState('');
  const [rulesOnly, setRulesOnly] = useState(false);
  const ctl = useRef<AbortController | null>(null);

  useEffect(() => { let on = true; void getSample().then((s) => { if (on) setCan(!!s); }); return () => { on = false; }; }, []);
  useEffect(() => { const id = window.setTimeout(() => setWaited(true), 2500); return () => window.clearTimeout(id); }, []);
  useEffect(() => () => ctl.current?.abort(), []);

  const aiCount = tenders.filter((t) => ai[t.номер]).length;
  const withPos = tenders;
  const res = (t: Tender) => ai[t.номер] || rules[t.номер];

  const run = async () => {
    setMsg(''); setRulesOnly(false);
    ctl.current = new AbortController();
    const out = { ...ai };
    let i = 0;
    try {
      for (const t of withPos) {
        i++;
        if (out[t.номер]) continue;
        setBusy(`ИИ проверяет тендер ${i} из ${withPos.length}…`);
        out[t.номер] = await analyzeWithAi(t, catalog, ctl.current.signal);
        onAi({ ...out });
      }
      setMsg('');
    } catch (e) {
      onAi({ ...out });
      if (e instanceof AiError && e.kind === 'not_granted') { setCan(false); setMsg('ИИ не разрешён для этой страницы — работаем по правилам.'); }
      else if (e instanceof AiError && e.kind === 'rate_limited') setMsg('Слишком много запросов к ИИ. Подождите минуту и нажмите «Продолжить с ИИ». Пока видна сверка по правилам.');
      else setMsg('ИИ ответил не так, как ждали. Показана сверка по правилам; можно попробовать ещё раз.');
    } finally { setBusy(''); }
  };

  const label = aiCount === 0 ? 'правила' : aiCount >= withPos.length ? 'ИИ (Claude)' : `ИИ (Claude) для ${aiCount} из ${withPos.length}, остальное правила`;
  const needStart = can === true && aiCount === 0 && !rulesOnly && !busy;

  return (
    <div>
      <Head n="05" rubric="Анализ" title="Анализ" />
      <div className={'modebar' + (aiCount ? ' ai' : '')} role="status" aria-live="polite">
        <span className="modetag">Сверка: {label}</span>
        {busy ? (
          <span className="btnrow"><span className="mono">{busy}</span><button className="btn sm" onClick={() => ctl.current?.abort()}>Стоп</button></span>
        ) : can === true && aiCount > 0 && aiCount < withPos.length ? (
          <button className="btn sm" onClick={() => void run()}>Продолжить с ИИ</button>
        ) : can === true && aiCount === 0 && rulesOnly ? (
          <button className="btn sm" onClick={() => void run()}>Проверить с ИИ</button>
        ) : null}
      </div>
      {needStart ? (
        <div className="empty" style={{ borderStyle: 'solid' }}>
          <p style={{ fontSize: 20, fontWeight: 600 }}>Проверим ассортимент с ИИ?</p>
          <p className="hint">Claude сверит характеристики и подскажет, что проверить. Первый раз спросит разрешение. Без ИИ работает сверка по правилам.</p>
          <div className="btnrow" style={{ marginTop: 14 }}>
            <button className="btn primary" onClick={() => void run()}>Начать анализ</button>
            <button className="btn" onClick={() => setRulesOnly(true)}>Только по правилам</button>
          </div>
        </div>
      ) : null}
      {msg ? <p className="err" role="alert">{msg}</p> : null}
      {can === false && !needStart ? <p className="hint">ИИ доступен, когда страница открыта на claude.ai. Сейчас работает сверка по правилам.</p> : null}
      {can === null && !waited ? <p className="hint" role="status">Проверяем, доступен ли ИИ…</p> : null}
      {!needStart && !(can === null && !waited) ? tenders.map((t) => <TenderBlock key={t.номер} t={t} res={res(t)} />) : null}
    </div>
  );
}
