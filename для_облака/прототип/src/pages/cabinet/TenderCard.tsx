import { useMemo, useState } from 'react';
import { Badge, DemoMark, Frame, SectionHead, SourceNote, Status } from '../../components/ui';
import { analyzeTz, getMode } from '../../ai';
import { recheck, SAMPLE_TZ } from '../../ai/rules';
import { getTenderView, NICHE_NAMES, priceSource, sverkaViews } from '../../data';
import { expectedParticipants, lookupPrice, proposal } from '../../lib/price';
import { findItem, matchHint } from '../../lib/match';
import { num, pct, rub, rubShort } from '../../lib/format';
import { href } from '../../router';
import { useApp } from '../../state';
import type { CatalogItem, Sverka, TenderView } from '../../types';

export default function TenderCard({ id }: { id?: string }) {
  const t = getTenderView(id);
  if (!t) {
    return (
      <>
        <SectionHead n={3} kicker="Демо-кабинет · раздел 3 из 5" title="Карточка тендера" />
        <p>Такой закупки нет в демо-данных. Выберите закупку из списка:</p>
        <ul className="ready-list">{sverkaViews.map((v) => <li key={v.key}><a href={href(`/demo/tender/${v.key}`)}>{v.предмет}</a></li>)}</ul>
        <p><a href={href('/demo/tendery')}>Все подходящие тендеры →</a></p>
      </>
    );
  }
  return <Card t={t} />;
}

function Card({ t }: { t: TenderView }) {
  const { catalog, isSample } = useApp();
  const [custom, setCustom] = useState<Sverka | null>(null);
  const [rechecked, setRechecked] = useState(false);
  const base = t.sverka;
  const sverka = custom || (base && rechecked ? recheck(base, catalog) : base);

  return (
    <>
      <div className="card-head">
        <div className="card-kickers">
          <span className="kicker">Демо-кабинет · раздел 3 из 5 · карточка тендера</span>
          <DemoMark>{t.kind === 'сверка' ? t.источник : 'реальная закупка, завершена'}</DemoMark>
        </div>
        <h1 className="card-title">{t.предмет}</h1>
        <p className="card-customer">{t.заказчик}{t.инн_заказчика ? `, ИНН ${t.инн_заказчика}` : ''} · {t.регион}</p>
        <dl className="facts">
          {t.номер && <div><dt>Номер</dt><dd className="mono">{t.номер}</dd></div>}
          <div><dt>НМЦ (начальная цена)</dt><dd>{rub(t.нмц)}</dd></div>
          <div><dt>Закон и способ</dt><dd>{t.закон}, {t.способ}</dd></div>
          <div><dt>Окончание подачи</dt><dd>{t.дата_окончания}</dd></div>
          <div><dt>Обеспечение заявки</dt><dd>{rub(t.обеспечение_заявки)}</dd></div>
          <div><dt>Обеспечение контракта</dt><dd>{rub(t.обеспечение_контракта)}</dd></div>
          <div><dt>Статус</dt><dd>{t.статус}</dd></div>
        </dl>
        <div className="badges">{t.бейджи.map((b, i) => <Badge key={i} b={b} />)}</div>
        <div className="cta-row">
          <a className="btn btn-solid" href={href(`/demo/zayavka/${t.key}`)}>Собрать черновик заявки</a>
          <a className="btn" href={href(`/demo/sroki/${t.key}`)}>Сроки и деньги</a>
        </div>
      </div>

      <section className="card-section">
        <SectionHead n={1} kicker="Сверка техзадания с ассортиментом" title="Что из техзадания закрывает ваш склад" />
        {sverka ? (
          <>
            <SverkaSummary s={sverka} />
            <div className="recheck">
              {custom ? (
                <><span>Показан разбор вставленного текста ({custom.режим === 'живой' ? 'Claude' : 'демо-правила'}).</span> <button type="button" className="btn btn-small" onClick={() => setCustom(null)}>Вернуть исходную сверку</button></>
              ) : base && (
                rechecked
                  ? <><span>Пересчитано по текущему ассортименту простыми правилами.</span> <button type="button" className="btn btn-small" onClick={() => setRechecked(false)}>Показать исходную сверку</button></>
                  : <><span>Сверка: {t.источник}.</span> <button type="button" className="btn btn-small" onClick={() => setRechecked(true)}>Пересчитать по {isSample ? 'текущему (примеру)' : 'вашему'} ассортименту</button></>
              )}
            </div>
            <SverkaTable s={sverka} catalog={catalog} />
          </>
        ) : (
          <NoSverka t={t} catalog={catalog} />
        )}
        <TzBox t={t} onResult={setCustom} hasBase={Boolean(base)} />
      </section>

      <section className="card-section">
        <SectionHead n={2} kicker="Нацрежим" title="Что проверить по российскому происхождению" />
        <NatReg t={t} s={sverka} catalog={catalog} />
      </section>

      <section className="card-section">
        <SectionHead n={3} kicker="Цена" title="Какую цену предложить" />
        <PriceBlock t={t} s={sverka} catalog={catalog} />
      </section>

      <section className="card-section">
        <SectionHead n={4} kicker="Риски" title="На что обратить внимание" />
        <Risks t={t} s={sverka} />
      </section>

      <div className="cta-row card-bottom">
        <a className="btn btn-solid" href={href(`/demo/zayavka/${t.key}`)}>Собрать черновик заявки →</a>
        <a className="btn" href={href('/demo/tendery')}>← К списку тендеров</a>
      </div>
    </>
  );
}

function SverkaSummary({ s }: { s: Sverka }) {
  const total = s.позиции.length || 1;
  return (
    <div className="tally" role="group" aria-label="Итог сверки">
      <div className="tally-item ok"><Status s="подходит" /><b>{s.итог.подходит}</b></div>
      <div className="tally-item almost"><Status s="почти" /><b>{s.итог.почти}</b></div>
      <div className="tally-item no"><Status s="нет" /><b>{s.итог.нет}</b></div>
      <div className="tally-bar" aria-hidden="true">
        <span className="ok" style={{ width: `${(s.итог.подходит / total) * 100}%` }} />
        <span className="almost" style={{ width: `${(s.итог.почти / total) * 100}%` }} />
        <span className="no" style={{ width: `${(s.итог.нет / total) * 100}%` }} />
      </div>
    </div>
  );
}

function condText(c: Sverka['позиции'][number]['характеристики'][number]) {
  const u = c.единица ? ` ${c.единица}` : '';
  const v = c.условие === '>=' ? `≥ ${c.значение}${u}` : c.условие === '<=' ? `≤ ${c.значение}${u}` : c.условие === 'из_списка' ? `${c.значение.replace(/;\s*/g, ' / ')}` : `${c.значение}${u}`;
  return `${c.имя}: ${v}${c.эквивалент_допускается ? '' : ' (без эквивалента)'}`;
}

export function SverkaTable({ s, catalog }: { s: Sverka; catalog: CatalogItem[] }) {
  return (
    <ol className="sverka-list">
      {s.позиции.map((p) => {
        const item = findItem(catalog, p.сверка.артикул, p.сверка.товар_из_каталога);
        const cls = p.сверка.статус === 'подходит' ? 'ok' : p.сверка.статус === 'почти' ? 'almost' : 'no';
        return (
          <li key={p['№']} className={`sv-row sv-${cls}`}>
            <div className="sv-num" aria-hidden="true">{p['№']}</div>
            <div className="sv-pos">
              <h4>{p.наименование} <span className="qty">{num(p.количество)} {p.единица}</span></h4>
              {(p.окпд2 || p.ктру) && <div className="codes mono">{p.окпд2 && `ОКПД2 ${p.окпд2}`}{p.ктру && ` · КТРУ ${p.ктру}`}</div>}
              <ul className="reqs">{p.характеристики.map((c, i) => <li key={i}>{condText(c)}</li>)}</ul>
            </div>
            <div className="sv-result">
              <Status s={p.сверка.статус} />
              {p.сверка.товар_из_каталога ? (
                <p className="sv-item"><b>{p.сверка.товар_из_каталога}</b>{p.сверка.артикул && <span className="mono"> · {p.сверка.артикул}</span>}{item?.цена ? <span> · {rub(item.цена)}/шт</span> : null}</p>
              ) : <p className="sv-item">Подходящего товара нет в ассортименте.</p>}
              {p.сверка.расхождения.length > 0 && p.сверка.статус !== 'нет' && (
                <ul className="diffs">
                  {p.сверка.расхождения.map((d, i) => <li key={i}><b>{d.характеристика}:</b> нужно {d.требуется}, у товара {d.у_товара}</li>)}
                </ul>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}

function NoSverka({ t, catalog }: { t: TenderView; catalog: CatalogItem[] }) {
  const hint = matchHint(t.предмет, catalog);
  return (
    <Frame className="no-sverka">
      <p><b>Техзадания этой закупки в демо нет</b> — в выгрузке Тендерплана только название. В рабочей версии документ скачивается с площадки и разбирается автоматически.</p>
      {hint.count > 0 ? (
        <p>По названию закупки в вашем ассортименте может подойти: {hint.categories.map((c) => `${c.категория.toLowerCase()} (${c.n})`).join(', ')}. Это подсказка, а не сверка.</p>
      ) : <p>По названию закупки подходящих категорий в ассортименте не нашли.</p>}
      <p>Посмотрите, как выглядит полная сверка: {sverkaViews.slice(0, 2).map((v, i) => <span key={v.key}>{i > 0 && ' · '}<a href={href(`/demo/tender/${v.key}`)}>{v.предмет}</a></span>)}.</p>
    </Frame>
  );
}

function TzBox({ t, onResult, hasBase }: { t: TenderView; onResult: (s: Sverka) => void; hasBase: boolean }) {
  const { catalog } = useApp();
  const [open, setOpen] = useState(!hasBase);
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const mode = getMode();
  async function run() {
    setBusy(true); setErr('');
    try {
      const r = await analyzeTz(text, catalog, { предмет: t.предмет, заказчик: t.заказчик, закон: t.закон, способ: t.способ, нмц: t.нмц || 0 });
      if (!r.позиции.length) throw new Error('Не нашли позиций. В демо-режиме каждая позиция — строка вида «1. Ноутбук — 5 шт», характеристики — строки «Название: не менее 16 ГБ».');
      onResult(r);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Ошибка разбора');
    } finally {
      setBusy(false);
    }
  }
  return (
    <details className="tz-box" open={open} onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)}>
      <summary>Разобрать своё техзадание {mode === 'живой' ? '(Claude, живой режим)' : '(демо-режим: простые правила)'}</summary>
      <p className="hint">Вставьте текст описания объекта закупки. {mode === 'живой'
        ? 'Текст и ваш ассортимент уйдут в Claude API с ключом из переменной окружения — только для локального теста.'
        : 'Ключа Claude API нет, поэтому работают простые правила: они понимают аккуратные строки. Настоящий разбор — в рабочей версии.'}</p>
      <label className="sr-only" htmlFor="tz-text">Текст техзадания</label>
      <textarea id="tz-text" rows={8} value={text} onChange={(e) => setText(e.target.value)} placeholder={'1. Ноутбук — 5 шт\nОбъём оперативной памяти: не менее 16 ГБ'} />
      <div className="cta-row">
        <button type="button" className="btn btn-solid" disabled={busy || !text.trim()} onClick={run}>{busy ? 'Разбираю…' : 'Разобрать и сверить'}</button>
        <button type="button" className="btn" onClick={() => setText(SAMPLE_TZ)}>Вставить пример техзадания</button>
      </div>
      {err && <p className="form-error" role="alert">{err}</p>}
    </details>
  );
}

function NatReg({ t, s, catalog }: { t: TenderView; s?: Sverka | null; catalog: CatalogItem[] }) {
  return (
    <div className="natreg">
      <p>Для компьютерной техники, оборудования связи, аудио-видеотехники и измерительных приборов могут действовать <b>запрет</b>, <b>ограничение</b> или <b>преимущество</b> для российских товаров — по постановлению Правительства РФ от 23.12.2024 № 1875 («национальный режим»). Какая мера действует, сказано в извещении {t.закон === '223-ФЗ' ? 'и документации о закупке' : 'о закупке'}.</p>
      <ol className="check-steps">
        <li>Найти в извещении, какая мера применяется: запрет, ограничение или преимущество.</li>
        <li>Проверить коды ОКПД2 и КТРУ позиций: попадают ли они в перечни постановления № 1875.</li>
        <li>Проверить товар в реестрах: российской промышленной продукции (ГИСП), российской радиоэлектронной продукции, евразийской промышленной продукции.</li>
        <li>Выписать номер реестровой записи и срок её действия — их указывают в заявке.</li>
        <li>При запрете иностранный товар не подавать. При преимуществе у российского товара выгода при сравнении цен — размер в извещении.</li>
      </ol>
      {s && (
        <div className="table-scroll" tabIndex={0} role="region" aria-label="Происхождение товаров">
          <table className="data-table stack-sm">
            <thead><tr><th scope="col">Позиция</th><th scope="col">Товар</th><th scope="col">Страна (из прайса)</th><th scope="col">Что сделать</th></tr></thead>
            <tbody>
              {s.позиции.filter((p) => p.сверка.статус !== 'нет').map((p) => {
                const item = findItem(catalog, p.сверка.артикул, p.сверка.товар_из_каталога);
                const ru = item && /росси/i.test(item.страна);
                return (
                  <tr key={p['№']}>
                    <td data-label="Позиция"><b>{p.наименование}</b></td>
                    <td data-label="Товар">{p.сверка.товар_из_каталога}</td>
                    <td data-label="Страна (из прайса)">{item?.страна || 'нет в прайсе'}</td>
                    <td data-label="Что сделать">{ru ? 'Найти номер реестровой записи в ГИСП и срок действия' : 'Иностранный товар: при запрете не подходит — подобрать российский аналог'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      <SourceNote>Подсказка, а не вывод. Не юридическая консультация: меру и перечни проверяют по извещению и тексту постановления.</SourceNote>
    </div>
  );
}

function PriceBlock({ t, s, catalog }: { t: TenderView; s?: Sverka | null; catalog: CatalogItem[] }) {
  const exp = expectedParticipants(t);
  const found = lookupPrice(t.ниша, t.закон, t.способ, exp.n);
  const nmc = t.нмц || 0;
  const costFromCatalog = useMemo(() => {
    if (!s) return null;
    let sum = 0, covered = 0;
    for (const p of s.позиции) {
      if (p.сверка.статус === 'нет') continue;
      const it = findItem(catalog, p.сверка.артикул, p.сверка.товар_из_каталога);
      if (it?.цена) { sum += it.цена * p.количество; covered++; }
    }
    return covered ? { sum, covered } : null;
  }, [s, catalog]);
  const [cost, setCost] = useState<number>(() => Math.round(costFromCatalog?.sum ?? nmc * 0.72));
  if (!found || !nmc) return <p>Для этой закупки нет данных о цене.</p>;
  const row = found.row;
  const pr = proposal(nmc, row);
  const maxDrop = Math.max(50, Math.ceil((row['p75_%'] + 10) / 10) * 10, (t['снижение_%'] || 0) + 5);
  const x = (d: number) => `${Math.min(100, (d / maxDrop) * 100)}%`;
  const h = t.история_заказчика;
  const margin = (price: number) => price - cost;
  const marginPct = (price: number) => (price > 0 ? ((price - cost) / price) * 100 : 0);
  const partOfNmcCovered = s && costFromCatalog ? `${costFromCatalog.covered} из ${s.позиции.length} поз. (без позиций «нет товара»)` : '';

  return (
    <div className="price-block">
      <div className="price-grid">
        <Frame ornate className="price-main">
          <div className="kicker">Предлагаемый диапазон</div>
          <p className="price-range"><b>{rubShort(pr.low)}</b> — <b>{rubShort(pr.high)}</b></p>
          <p>Середина (медиана): <b>{rub(pr.mid)}</b>, это снижение на {pct(row['медиана_снижения_%'])} от НМЦ.</p>
          <div className="range-bar" role="img" aria-label={`Снижение цены в похожих закупках: от ${pct(row['p25_%'])} до ${pct(row['p75_%'])}, медиана ${pct(row['медиана_снижения_%'])}`}>
            <div className="rb-track" />
            <div className="rb-band" style={{ left: x(row['p25_%']), width: `calc(${x(row['p75_%'])} - ${x(row['p25_%'])})` }} />
            <div className="rb-mid" style={{ left: x(row['медиана_снижения_%']) }} />
            {t['снижение_%'] !== null && <div className="rb-fact" style={{ left: x(t['снижение_%']) }}><span>факт −{pct(t['снижение_%'], 0)}</span></div>}
            <div className="rb-scale"><span>0%</span><span>−{maxDrop / 2}%</span><span>−{maxDrop}%</span></div>
          </div>
          <p className="hint">Полоса — где оказалась половина похожих закупок (от {pct(row['p25_%'])} до {pct(row['p75_%'])} снижения). Чёрная черта — медиана.{t['снижение_%'] !== null ? ' Красная — сколько снизил цену победитель в этой закупке на самом деле.' : ''}</p>
        </Frame>
        <div className="price-facts">
          <h4>На чём основано</h4>
          <ul>
            <li>Похожие закупки: {NICHE_NAMES[t.ниша].toLowerCase()}, {row.закон === 'все' ? 'оба закона' : row.закон}, {row.способ === 'все' || row.способ === 'все способы' ? 'все способы' : row.способ.toLowerCase()}, участников: {row.участников} — <b>{num(row.n)} закупок</b>.</li>
            <li>Ожидаем участников: {exp.n} — {exp.why}.</li>
            {h && <li>У этого заказчика в выгрузке {h.закупок_в_выгрузке} {h.закупок_в_выгрузке === 1 ? 'закупка' : 'закупок'}: медиана снижения {pct(h['медиана_снижения_%'])}, участников обычно {num(h.медиана_участников, 1)}, с одним участником — {pct(h['доля_с_одним_участником_%'], 0)}.</li>}
            {!h && <li>Истории этого заказчика в выгрузке нет.</li>}
            <li>Ячейка таблицы: {found.level}.</li>
          </ul>
          <SourceNote>Источник: {priceSource}. Оценка по данным, не гарантия победы.</SourceNote>
        </div>
      </div>

      <div className="margin">
        <h4>Ваша маржа</h4>
        <label className="inline-field">Себестоимость поставки, ₽
          <input type="number" min={0} step={1000} value={cost} onChange={(e) => setCost(Number(e.target.value) || 0)} />
        </label>
        <p className="hint">{costFromCatalog ? `Посчитано по ценам из прайса: ${partOfNmcCovered}. Добавьте доставку и прочие расходы.` : 'Пример: 72% от НМЦ. Введите свою себестоимость.'}</p>
        <div className="table-scroll" tabIndex={0} role="region" aria-label="Маржа">
          <table className="data-table margin-table">
            <thead><tr><th scope="col">Цена</th><th scope="col" className="num">Сумма</th><th scope="col" className="num">Маржа</th><th scope="col" className="num">Маржа, %</th></tr></thead>
            <tbody>
              {([['Смело (сильное снижение)', pr.low], ['Медиана', pr.mid], ['Осторожно (слабое снижение)', pr.high], ['По НМЦ', nmc]] as [string, number][]).map(([l, p]) => (
                <tr key={l} className={margin(p) < 0 ? 'neg' : ''}><td>{l}</td><td className="num">{rub(p)}</td><td className="num">{rub(margin(p))}</td><td className="num">{pct(marginPct(p))}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function Risks({ t, s }: { t: TenderView; s?: Sverka | null }) {
  const items = [...t.риски];
  if (t.бейджи.some((b) => b.код === 'svoy')) {
    const b = t.бейджи.find((x) => x.код === 'svoy')!;
    items.unshift(`Возможна закупка «под своего»: ${b.почему}.`);
  }
  if (s && s.итог.нет > 0 && !items.some((x) => x.includes('Не хватает'))) items.push(`Нет товара по ${s.итог.нет} поз. — нужен партнёр или отказ, если частичная поставка не разрешена.`);
  if (s && s.итог.почти > 0) items.push(`${s.итог.почти} поз. «почти»: заменить товар или задать заказчику вопрос (запрос на разъяснение) до окончания подачи.`);
  if (t.kind === 'выгрузка') items.push('Срок подачи в демо не считаем: в выгрузке нет даты публикации извещения.');
  return items.length ? (
    <ul className="risks">{items.map((r, i) => <li key={i}>{r}</li>)}</ul>
  ) : <p>Явных рисков по данным не видно.</p>;
}
