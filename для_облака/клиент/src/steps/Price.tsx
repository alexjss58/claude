import { useRef, useState } from 'react';
import type { Contact } from '../state';
import type { Tender, TenderResult } from '../types';
import { PARTS, defaultParts, estimate, priceAt, type Parts } from '../lib/price';
import { MODE_TITLE } from '../lib/natreg';
import { natOf, risksOf } from '../lib/risks';
import { num, pct, rub, rubShort } from '../lib/format';
import { saveFile } from '../lib/save';
import { Head } from './ui';

/** Себестоимость по ценам прайса × количество: только для закрытых («подходит» и «почти») позиций */
export function costFromCatalog(res: TenderResult): { cost: number | null; partial: boolean } {
  if (res.noPositions) return { cost: null, partial: false }; // количество в ТЗ неизвестно
  const used = res.positions.filter((p) => p.status !== 'нет' && p.item);
  if (!used.length) return { cost: null, partial: false };
  const priced = used.filter((p) => p.item!.price != null);
  if (!priced.length) return { cost: null, partial: false };
  const cost = priced.reduce((s, p) => s + p.item!.price! * (p.qty || 1), 0);
  return { cost, partial: priced.length < res.positions.length || res.noPositions };
}

export interface Calc {
  t: Tender; res: TenderResult; parts: Parts; est: ReturnType<typeof estimate>; cost: number | null; partial: boolean; auto: boolean;
}

export function calcFor(t: Tender, res: TenderResult, participants: Record<string, string>, costs: Record<string, string>): Calc {
  const parts = (participants[t.номер] as Parts) || defaultParts(t);
  const auto = costFromCatalog(res);
  const manual = costs[t.номер];
  const manualNum = manual != null && manual.trim() !== '' ? Number(manual.replace(/\s/g, '').replace(',', '.')) : null;
  const cost = manualNum != null && Number.isFinite(manualNum) ? manualNum : manual != null && manual.trim() === '' ? null : auto.cost;
  return { t, res, parts, est: estimate(t, parts), cost, partial: manualNum == null && auto.partial, auto: manualNum == null && auto.cost != null };
}

function margin(price: number, cost: number | null): string {
  if (cost == null || !price) return '—';
  return pct(((price - cost) / price) * 100, 1);
}

const csvCell = (v: string | number | null | undefined) => {
  const s = v == null ? '' : String(v);
  return /[;"\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
};

export function buildCsv(calcs: Calc[], company: string): string {
  const head = ['Номер', 'Предмет', 'Заказчик', 'Регион', 'Закон', 'Способ', 'НМЦ, ₽', 'Подходит позиций', 'Всего позиций', 'Нацрежим', 'Риски', 'Участников (оценка)', 'Цена от, ₽', 'Цена до, ₽', 'Снижение, %', 'Себестоимость, ₽', 'Маржа на нижней цене, %', 'Ссылка в ЕИС'];
  const rows = calcs.map((c) => {
    const nat = natOf(c.t);
    const lo = c.est ? priceAt(c.t.нмц, c.est.p75Pct) : null, hi = c.est ? priceAt(c.t.нмц, c.est.medianPct) : null;
    return [c.t.номер, c.t.предмет, c.t.заказчик, c.t.регион, c.t.закон, c.t.способ, c.t.нмц, c.res.closed, c.res.total, nat ? MODE_TITLE[nat.info.mode] : '', risksOf(c.t).join(' | '), c.parts,
      lo, hi, c.est ? `${c.est.medianPct}–${c.est.p75Pct}` : '', c.cost != null ? Math.round(c.cost) : '', lo != null && c.cost != null ? ((lo - c.cost) / lo * 100).toFixed(1) : '', c.t.ссылка];
  });
  const lines = [[`Тендер под ключ: итог для «${company || 'компании'}»`], head, ...rows].map((r) => r.map(csvCell).join(';'));
  return '﻿' + lines.join('\r\n') + '\r\n';
}

export function Price({ calcs, company, participants, costs, contact, onParts, onCost, onContact }: {
  calcs: Calc[]; company: string; participants: Record<string, string>; costs: Record<string, string>; contact: Contact;
  onParts: (n: string, p: Parts) => void; onCost: (n: string, v: string) => void; onContact: (c: Contact) => void;
}) {
  const [csvMsg, setCsvMsg] = useState('');
  const [err, setErr] = useState('');
  const formRef = useRef<HTMLDivElement>(null);
  void participants; void costs;

  const submit = () => {
    if (contact.value.trim().length < 5) { setErr('Оставьте телефон или Telegram'); return; }
    if (!contact.consent) { setErr('Нужно согласие на обработку данных'); return; }
    setErr('');
    // ПОДКЛЮЧИТЬ ОТПРАВКУ: здесь отправьте заявку (например fetch POST на свой сервер или в бота Telegram):
    // { контакт: contact.value, компания: company, тендеры: calcs.map((c) => c.t.номер) }.
    // Сейчас заявка только сохраняется в localStorage этого браузера (см. state.ts) и никуда не уходит.
    onContact({ ...contact, sent: true });
  };

  const download = async () => {
    const blob = new Blob([buildCsv(calcs, company)], { type: 'text/csv;charset=utf-8' });
    const r = await saveFile(blob, 'tendery_itog.csv');
    setCsvMsg(r === 'saved' ? 'Файл отдан браузеру' : r === 'declined' ? 'Вы отказались от сохранения' : 'Скачать здесь не получилось: откройте страницу в браузере');
  };

  return (
    <div>
      <Head n="06" rubric="Цена" title="Цена" />
      {calcs.map((c) => {
        const { t, est } = c;
        const lo = est ? priceAt(t.нмц, est.p75Pct) : null, hi = est ? priceAt(t.нмц, est.medianPct) : null;
        const mid = est ? priceAt(t.нмц, (est.medianPct + est.p25Pct) / 2) : null;
        const levels = est ? [
          { name: 'Осторожно', drop: est.p25Pct, price: priceAt(t.нмц, est.p25Pct), win: '1 из 4' },
          { name: 'Середина', drop: est.medianPct, price: priceAt(t.нмц, est.medianPct), win: 'около половины' },
          { name: 'Уверенно', drop: est.p75Pct, price: priceAt(t.нмц, est.p75Pct), win: '3 из 4' },
        ] : [];
        void mid;
        const costVal = costs[t.номер] ?? (c.cost != null ? String(Math.round(c.cost)) : '');
        return (
          <section className="pcard" key={t.номер} aria-label={t.предмет}>
            <div className="pcard-h">
              <h3>{t.предмет}</h3>
              <p className="mono dim" style={{ marginTop: 6 }}>НМЦ <strong style={{ fontWeight: 500 }}>{rub(t.нмц)}</strong> · {t.закон}</p>
            </div>
            <div className="pcard-b">
              <div className="field" role="radiogroup" aria-label="Сколько будет участников">
                <span className="lbl mono">Сколько участников ждать</span>
                <div className="seg parts">
                  {PARTS.map((p) => <button key={p} type="button" role="radio" aria-checked={c.parts === p} onClick={() => onParts(t.номер, p)}>{p}</button>)}
                </div>
                {!participants[t.номер] ? <p className="hint">Выбрано по медиане для ниши, можно поменять.</p> : null}
              </div>
              {est && lo != null && hi != null ? (
                <>
                  <p className="offer" style={{ marginTop: 18 }}>
                    Предложите <span className="hl">{num(Math.min(lo, hi))}–{num(Math.max(lo, hi))} ₽</span> (снижение {pct(est.medianPct)}–{pct(est.p75Pct)}).
                    При таком снижении в похожих закупках побеждали примерно в половине случаев (медиана) / в 3 из 4 (p75).
                  </p>
                  <p className="note" style={{ marginTop: 8 }}>Оценка по данным ЕИС/Тендерплана, не гарантия. Основа: {est.n} похожих закупок ({est.scope}){est.approxNiche ? `. Своей ниши в таблице нет, взяли ближайшую: «${est.nicheUsed}», точность ниже` : ''}.</p>
                  <table className="lv">
                    <thead><tr><th>Уровень</th><th className="r">Цена</th><th className="r">Снижение</th><th className="r">Маржа</th></tr></thead>
                    <tbody>
                      {levels.map((l) => (
                        <tr key={l.name} className={l.name === 'Середина' ? 'mid' : ''}>
                          <td>{l.name}<span className="hint" style={{ display: 'block', marginTop: 0, fontSize: 13.5 }}>побеждали: {l.win}</span></td>
                          <td className="r">{rub(l.price)}</td>
                          <td className="r">{pct(l.drop)}</td>
                          <td className="r">{margin(l.price, c.cost)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </>
              ) : <p className="hint" style={{ marginTop: 16 }}>Для этой ниши нет таблицы цен — ориентируйтесь на НМЦ и свою себестоимость.</p>}
              <label className="field" style={{ marginTop: 18 }}>
                <span className="lbl mono">Ваша себестоимость, ₽</span>
                <input className="input" inputMode="decimal" value={costVal} placeholder="Например 1 200 000" autoComplete="off"
                  onChange={(e) => onCost(t.номер, e.target.value.replace(/[^\d\s.,]/g, ''))} />
                <span className="hint" style={{ display: 'block' }}>
                  {c.auto ? `Посчитана по ценам вашего прайса × количество${c.partial ? ' — только по позициям с ценой, остальные добавьте' : ''}.` : c.res.noPositions ? 'Количество в ТЗ пока неизвестно — введите себестоимость вручную, и покажем маржу.' : 'В прайсе нет цен по этому тендеру — введите вручную, и покажем маржу.'}
                </span>
              </label>
            </div>
          </section>
        );
      })}

      <section className="final" aria-label="Итог">
        <h2 className="h1" style={{ fontSize: 36 }}>Итог</h2>
        <ul className="sumlist">
          {calcs.map((c) => (
            <li key={c.t.номер}>
              <p className="sumt">{c.t.предмет.length > 80 ? c.t.предмет.slice(0, 79) + '…' : c.t.предмет}</p>
              <p className="hint" style={{ marginTop: 2 }}>НМЦ {rubShort(c.t.нмц)} · закрываете {c.res.closed} из {c.res.total}</p>
              <p className="sump">{c.est ? <>Предложить: <strong>{num(priceAt(c.t.нмц, c.est.p75Pct))}–{num(priceAt(c.t.нмц, c.est.medianPct))} ₽</strong></> : 'Цена: ориентируйтесь на НМЦ'}</p>
            </li>
          ))}
        </ul>

        <div ref={formRef} id="apply" style={{ marginTop: 30 }}>
          {contact.sent ? (
            <div className="thanks" role="status">Спасибо, свяжемся. <span className="hint" style={{ display: 'block' }}>Контакт: {contact.value}</span></div>
          ) : (
            <div className="field">
              <h2 className="h1" style={{ fontSize: 30, marginBottom: 14 }}>Хочу подать с вами</h2>
              <label className="lbl mono" htmlFor="contact">Телефон или Telegram</label>
              <input id="contact" className="input" value={contact.value} placeholder="+7 900 000-00-00 или @username" autoComplete="tel" inputMode="text"
                aria-invalid={!!err && contact.value.trim().length < 5} onChange={(e) => onContact({ ...contact, value: e.target.value })} />
              <div className="consent">
                <button type="button" role="checkbox" aria-checked={contact.consent} aria-label="Согласие на обработку данных" onClick={() => onContact({ ...contact, consent: !contact.consent })}>
                  <span className={'box' + (contact.consent ? ' on' : '')} aria-hidden="true" style={{ width: 22, height: 22 }} />
                </button>
                <span>Согласен на обработку моих персональных данных (имя компании, контакт) для связи по подаче заявки. Данные не передаются третьим лицам.</span>
              </div>
              {err ? <p className="err" role="alert">{err}</p> : null}
              <div className="btnrow" style={{ marginTop: 16 }}>
                <button className="btn fill" type="button" onClick={submit}>Отправить контакт</button>
              </div>
            </div>
          )}
        </div>
        <div className="btnrow" style={{ marginTop: 20 }}>
          <button className="btn" type="button" onClick={() => void download()}>Скачать итог (CSV)</button>
        </div>
        {csvMsg ? <p className="hint" role="status">{csvMsg}</p> : null}
        <p className="disc">Цены и шансы — оценка по данным ЕИС и Тендерплана, не гарантия. Нацрежим и риски — подсказка, не юридическая консультация.</p>
      </section>
    </div>
  );
}
