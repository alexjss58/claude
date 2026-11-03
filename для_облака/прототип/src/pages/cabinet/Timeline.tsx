import { useMemo, useState } from 'react';
import { DemoMark, Frame, SectionHead, SourceNote } from '../../components/ui';
import { getTenderView, sverkaViews } from '../../data';
import { buildTimeline } from '../../lib/timeline';
import { expectedParticipants, lookupPrice, proposal } from '../../lib/price';
import { findItem } from '../../lib/match';
import { dateLong, parseRuDate, rub } from '../../lib/format';
import { useApp } from '../../state';
import { TenderPicker } from './Draft';

export default function Timeline({ id }: { id?: string }) {
  const t = getTenderView(id) || sverkaViews[0];
  return <TimelineInner key={t?.key} id={t?.key} />;
}

function TimelineInner({ id }: { id?: string }) {
  const { catalog } = useApp();
  const t = getTenderView(id)!;
  const nmc = t.нмц || 0;
  const defaults = useMemo(() => {
    const f = lookupPrice(t.ниша, t.закон, t.способ, expectedParticipants(t).n);
    const price = f ? Math.round(proposal(nmc, f.row).mid) : nmc;
    let cost = 0;
    if (t.sverka) {
      for (const p of t.sverka.позиции) {
        if (p.сверка.статус === 'нет') continue;
        const it = findItem(catalog, p.сверка.артикул, p.сверка.товар_из_каталога);
        if (it?.цена) cost += it.цена * p.количество;
      }
    }
    if (!cost) cost = Math.round(nmc * 0.72);
    // Обеспечение: из выгрузки, если есть; иначе — пример (1% заявки, 5% контракта), его можно поменять.
    const bid = t.обеспечение_заявки ?? Math.round(nmc * 0.01);
    const contract = t.обеспечение_контракта ?? Math.round(nmc * 0.05);
    return { price, cost, bid, contract };
  }, [t, nmc, catalog]);

  const [price, setPrice] = useState(defaults.price);
  const [cost, setCost] = useState(defaults.cost);
  const [bid, setBid] = useState(defaults.bid);
  const [contract, setContract] = useState(defaults.contract);
  const [delivery, setDelivery] = useState(30);
  const [acceptance, setAcceptance] = useState(10);
  const [payment, setPayment] = useState(7);
  const [rate, setRate] = useState(3);
  const [useG, setUseG] = useState(true);

  const today = new Date(2026, 10, 3);
  const parsed = parseRuDate(t.дата_окончания);
  // Для завершённых закупок дата подачи в прошлом — для примера считаем от ближайшей недели.
  const start = parsed && parsed >= today ? parsed : new Date(2026, 10, 10);
  const tl = useMemo(() => buildTimeline({
    start, law: t.закон, method: t.способ, deliveryDays: delivery, acceptanceWorkDays: acceptance, paymentWorkDays: payment,
    price, cost, bidSecurity: bid, contractSecurity: contract, guaranteeRate: rate, useGuarantee: useG,
  }), [start.getTime(), t.закон, t.способ, delivery, acceptance, payment, price, cost, bid, contract, rate, useG]); // eslint-disable-line react-hooks/exhaustive-deps

  const first = tl.steps[0].date, last = tl.steps[tl.steps.length - 1].date;
  const span = Math.max(1, last.getTime() - first.getTime());
  const pos = (d: Date) => ((d.getTime() - first.getTime()) / span) * 100;
  const totalDays = Math.round(span / 86400000);

  return (
    <>
      <SectionHead n={5} kicker="Демо-кабинет · раздел 5 из 5" title="Сроки и деньги" lead="От подачи заявки до оплаты: когда что происходит и сколько своих денег нужно в обороте." />
      <div className="draft-tools"><TenderPicker current={t.key} base="/demo/sroki" /></div>
      {!(parsed && parsed >= today) && <p className="hint"><DemoMark>пример</DemoMark> Эта закупка уже завершена — для расчёта берём подачу 10 ноября 2026.</p>}

      <div className="tl-summary">
        <Frame ornate className="tl-big"><span className="kicker">От подачи до оплаты</span><b>{totalDays} дн.</b><span>{dateLong(first)} → {dateLong(last)}</span></Frame>
        <Frame className="tl-big"><span className="kicker">Своих денег в обороте</span><b>{rub(tl.gap)}</b><span>товар{useG ? ' + гарантия' : ' + обеспечение'} до оплаты, около {tl.gapDays} дн. после поставки</span></Frame>
        <Frame className="tl-big"><span className="kicker">Прибыль до налогов</span><b className={tl.profit < 0 ? 'neg' : ''}>{rub(tl.profit)}</b><span>цена − себестоимость − гарантия</span></Frame>
      </div>

      <div className="gantt" role="img" aria-label={`Шкала: ${tl.steps.map((s) => `${s.title} — ${dateLong(s.date)}`).join('; ')}`}>
        <div className="gantt-line" />
        {tl.steps.map((s, i) => (
          <div key={s.key} className={`gantt-pt ${i % 2 ? 'down' : 'up'}`} style={{ left: `${pos(s.date)}%` }}>
            <span className="gantt-dot" />
            <span className="gantt-label"><b>{s.title}</b><br />{dateLong(s.date)}</span>
          </div>
        ))}
      </div>

      <ol className="timeline">
        {tl.steps.map((s, i) => (
          <li key={s.key} className="tl-step">
            <div className="tl-date"><span className="roman-sm">{i + 1}</span><b>{dateLong(s.date)}</b></div>
            <div className="tl-body">
              <h3>{s.title}</h3>
              <p>{s.note}</p>
              {s.money && s.money.amount > 0 && (
                <p className={`money money-${s.money.dir}`}>
                  <span className="money-sign" aria-hidden="true">{s.money.dir === 'in' ? '+' : s.money.dir === 'out' ? '−' : s.money.dir === 'hold' ? '⏸' : '↺'}</span>
                  <b>{rub(s.money.amount)}</b> — {s.money.label}
                </p>
              )}
            </div>
          </li>
        ))}
      </ol>

      <Frame className="tl-inputs">
        <h3>Ваши условия <DemoMark>введите свои</DemoMark></h3>
        <div className="form-grid">
          <label>Цена контракта, ₽<input type="number" value={price} min={0} step={1000} onChange={(e) => setPrice(Number(e.target.value) || 0)} /></label>
          <label>Себестоимость товара, ₽<input type="number" value={cost} min={0} step={1000} onChange={(e) => setCost(Number(e.target.value) || 0)} /></label>
          <label>Обеспечение заявки, ₽<input type="number" value={bid} min={0} step={100} onChange={(e) => setBid(Number(e.target.value) || 0)} /></label>
          <label>Обеспечение контракта, ₽<input type="number" value={contract} min={0} step={1000} onChange={(e) => setContract(Number(e.target.value) || 0)} /></label>
          <label>Срок поставки, календ. дней<input type="number" value={delivery} min={1} max={365} onChange={(e) => setDelivery(Number(e.target.value) || 1)} /></label>
          <label>Приёмка, рабочих дней<input type="number" value={acceptance} min={1} max={60} onChange={(e) => setAcceptance(Number(e.target.value) || 1)} /></label>
          <label>Оплата после приёмки, рабочих дней<input type="number" value={payment} min={1} max={60} onChange={(e) => setPayment(Number(e.target.value) || 1)} /></label>
          <label>Ставка банковской гарантии, % в год<input type="number" value={rate} min={0} max={30} step={0.5} onChange={(e) => setRate(Number(e.target.value) || 0)} /></label>
          <label className="check span2"><input type="checkbox" checked={useG} onChange={(e) => setUseG(e.target.checked)} /> Обеспечение контракта — банковской гарантией (иначе деньгами)</label>
        </div>
        <p className="hint">Обеспечение {t.обеспечение_контракта ? 'взято из выгрузки' : 'по умолчанию — пример: 1% заявки и 5% контракта от НМЦ'}. Ставка гарантии {rate}% — условный пример для расчёта, не рыночная ставка: уточните в банке.</p>
      </Frame>
      <SourceNote>Сроки — ориентиры по 44-ФЗ и 223-ФЗ; точные — в извещении, документации и проекте контракта. Праздники не учтены. Не юридическая консультация.</SourceNote>
    </>
  );
}
