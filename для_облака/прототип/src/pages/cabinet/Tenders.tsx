import { useMemo, useState } from 'react';
import { Badge, DemoMark, Frame, SectionHead, SourceNote, Status } from '../../components/ui';
import { NET_NOTE, NICHE_NAMES, regions, SOURCE_NOTE, sverkaFromEngine, sverkaSource, sverkaViews, tenderViews, tendersMeta } from '../../data';
import { matchHint } from '../../lib/match';
import { niceName, num, pct, rubShort, plural } from '../../lib/format';
import { href } from '../../router';
import { useApp } from '../../state';
import type { Badge as BadgeT, TenderView } from '../../types';

const SUMS: [string, number, number][] = [
  ['любая', 0, Infinity],
  ['до 300 тыс. ₽', 0, 300_000],
  ['300 тыс. – 1 млн ₽', 300_000, 1_000_000],
  ['1–5 млн ₽', 1_000_000, 5_000_000],
  ['больше 5 млн ₽', 5_000_000, Infinity],
];

const PAGE = 25;

export default function Tenders() {
  const { catalog } = useApp();
  const [niche, setNiche] = useState<'все' | 'svyaz' | 'pribory'>('все');
  const [law, setLaw] = useState<'все' | '44-ФЗ' | '223-ФЗ'>('все');
  const [sum, setSum] = useState(0);
  const [region, setRegion] = useState('все');
  const [q, setQ] = useState('');
  const [onlyFew, setOnlyFew] = useState(false);
  const [hideSvoy, setHideSvoy] = useState(false);
  const [onlyMatch, setOnlyMatch] = useState(false);
  const [sort, setSort] = useState<'date' | 'nmc' | 'match'>('match');
  const [limit, setLimit] = useState(PAGE);
  const [showAllReady, setShowAllReady] = useState(false);

  const withHints = useMemo(() => tenderViews.map((t) => ({ t, hint: matchHint(t.предмет, catalog) })), [catalog]);

  const list = useMemo(() => {
    const [, lo, hi] = SUMS[sum];
    const words = q.toLowerCase().split(/\s+/).filter(Boolean);
    const res = withHints.filter(({ t, hint }) => {
      if (niche !== 'все' && t.ниша !== niche) return false;
      if (law !== 'все' && t.закон !== law) return false;
      if (t.нмц !== null && (t.нмц < lo || t.нмц >= hi)) return false;
      if (region !== 'все' && t.регион !== region) return false;
      if (onlyFew && !t.бейджи.some((b) => b.код === 'few')) return false;
      if (hideSvoy && t.бейджи.some((b) => b.код === 'svoy')) return false;
      if (onlyMatch && hint.count === 0) return false;
      if (words.length) {
        const text = (t.предмет + ' ' + t.заказчик).toLowerCase();
        if (!words.every((w) => text.includes(w))) return false;
      }
      return true;
    });
    const dateNum = (s: string) => Number(s.split('.').reverse().join(''));
    res.sort((a, b) => sort === 'nmc' ? (b.t.нмц || 0) - (a.t.нмц || 0)
      : sort === 'match' ? (b.hint.count - a.hint.count) || dateNum(b.t.дата_окончания) - dateNum(a.t.дата_окончания)
      : dateNum(b.t.дата_окончания) - dateNum(a.t.дата_окончания));
    return res;
  }, [withHints, niche, law, sum, region, q, onlyFew, hideSvoy, onlyMatch, sort]);

  const reset = () => { setNiche('все'); setLaw('все'); setSum(0); setRegion('все'); setQ(''); setOnlyFew(false); setHideSvoy(false); setOnlyMatch(false); setLimit(PAGE); };

  return (
    <>
      <SectionHead n={2} kicker="Демо-кабинет · раздел 2 из 5" title="Подходящие тендеры" lead="Закупки по вашим нишам: только поставка товара, без монтажа, ремонта и услуг. Бейджи подсказывают, на что смотреть." />

      <Frame ornate className="ready-block">
        <div className="ready-head">
          <h3>{sverkaFromEngine ? `Реальные закупки со сверкой техзадания: ${sverkaViews.length}` : 'Готова сверка техзадания'}</h3>
          <DemoMark>{sverkaFromEngine ? 'сверка: демо-режим движка' : 'демо, пример'}</DemoMark>
        </div>
        <p className="hint">{sverkaSource}. Откройте карточку, чтобы увидеть сверку по позициям, нацрежим, цену, риски и черновик заявки.{sverkaFromEngine ? ` ${NET_NOTE}` : ''}</p>
        <ul className="ready-list">
          {(showAllReady ? sverkaViews : sverkaViews.slice(0, 6)).map((t) => <ReadyItem key={t.key} t={t} />)}
        </ul>
        {sverkaViews.length > 6 && (
          <button type="button" className="btn btn-small" onClick={() => setShowAllReady(!showAllReady)}>{showAllReady ? 'Свернуть список' : `Показать все ${sverkaViews.length}`}</button>
        )}
      </Frame>

      <h3 className="h3-rule">Закупки из выгрузки Тендерплана <DemoMark>завершённые</DemoMark></h3>
      <p className="hint">{String(tendersMeta.что_это)} {String(tendersMeta.правила_отбора)}</p>

      <form className="filters" onSubmit={(e) => e.preventDefault()} aria-label="Фильтры">
        <label>Ниша
          <select value={niche} onChange={(e) => { setNiche(e.target.value as typeof niche); setLimit(PAGE); }}>
            <option value="все">все</option>
            <option value="svyaz">{NICHE_NAMES.svyaz}</option>
            <option value="pribory">{NICHE_NAMES.pribory}</option>
          </select>
        </label>
        <label>Закон
          <select value={law} onChange={(e) => { setLaw(e.target.value as typeof law); setLimit(PAGE); }}>
            <option value="все">все</option><option>44-ФЗ</option><option>223-ФЗ</option>
          </select>
        </label>
        <label>Сумма (НМЦ)
          <select value={sum} onChange={(e) => { setSum(Number(e.target.value)); setLimit(PAGE); }}>
            {SUMS.map(([l], i) => <option key={l} value={i}>{l}</option>)}
          </select>
        </label>
        <label>Регион
          <select value={region} onChange={(e) => { setRegion(e.target.value); setLimit(PAGE); }}>
            <option value="все">все</option>
            {regions.map((r) => <option key={r}>{r}</option>)}
          </select>
        </label>
        <label className="grow">Слова в названии или заказчике
          <input type="search" value={q} placeholder="например: телефон" onChange={(e) => { setQ(e.target.value); setLimit(PAGE); }} />
        </label>
        <fieldset className="checks">
          <legend className="sr-only">Дополнительно</legend>
          <label className="check"><input type="checkbox" checked={onlyMatch} onChange={(e) => setOnlyMatch(e.target.checked)} /> есть в ассортименте</label>
          <label className="check"><input type="checkbox" checked={onlyFew} onChange={(e) => setOnlyFew(e.target.checked)} /> только «мало конкурентов»</label>
          <label className="check"><input type="checkbox" checked={hideSvoy} onChange={(e) => setHideSvoy(e.target.checked)} /> скрыть «под своего?»</label>
        </fieldset>
        <label>Порядок
          <select value={sort} onChange={(e) => setSort(e.target.value as typeof sort)}>
            <option value="match">с вашим товаром</option>
            <option value="date">новые</option>
            <option value="nmc">дорогие</option>
          </select>
        </label>
      </form>

      <div className="list-head" aria-live="polite">
        <span>Найдено: <b>{list.length}</b> {plural(list.length, 'закупка', 'закупки', 'закупок')}</span>
        <button type="button" className="btn btn-small" onClick={reset}>Сбросить фильтры</button>
      </div>

      <details className="legend">
        <summary>Что значат бейджи</summary>
        <ul>
          <li><Badge b={{ код: 'match', текст: 'есть в ассортименте', почему: '' }} /> по названию закупки в вашем прайсе есть товары этой категории (это подсказка, не сверка техзадания).</li>
          <li><Badge b={{ код: 'svoy', текст: 'под своего?', почему: '' }} /> марка или модель в названии без «или эквивалент», или у заказчика часто один участник и цена без снижения. Проверить, не под конкретного поставщика ли закупка.</li>
          <li><Badge b={{ код: 'natreg', текст: 'нацрежим', почему: '' }} /> группа товаров, где обычно действуют запреты, ограничения или преимущество для российской продукции (ПП РФ № 1875). Проверить по извещению.</li>
          <li><Badge b={{ код: 'few', текст: 'мало конкурентов', почему: '' }} /> в закупке был один участник или у заказчика обычно 1–2 участника.</li>
        </ul>
      </details>

      <ul className="tender-list">
        {list.slice(0, limit).map(({ t, hint }) => <TenderRow key={t.key} t={t} hintCount={hint.count} hintCats={hint.categories.map((c) => c.категория)} />)}
      </ul>
      {list.length > limit && (
        <div className="center"><button type="button" className="btn" onClick={() => setLimit(limit + PAGE)}>Показать ещё {Math.min(PAGE, list.length - limit)}</button></div>
      )}
      {list.length === 0 && <p className="empty">Ничего не нашли. Попробуйте ослабить фильтры.</p>}
      <SourceNote>Закупки: {SOURCE_NOTE}. Бейджи и подсказки считаются по названию закупки и истории заказчика в выгрузке — это не проверка документации.</SourceNote>
    </>
  );
}

function ReadyItem({ t }: { t: TenderView }) {
  const s = t.sverka!;
  return (
    <li>
      <a href={href(`/demo/tender/${t.key}`)} className="ready-item">
        <span className="ready-title">{t.предмет}</span>
        <span className="ready-meta">{niceName(t.заказчик)}</span>
        <span className="ready-meta">{t.закон} · {t.способ} · {rubShort(t.нмц)} · {t.регион}</span>
        <span className="ready-tally">
          <Status s="подходит" /> {s.итог.подходит}
          <Status s="почти" /> {s.итог.почти}
          <Status s="нет" /> {s.итог.нет}
        </span>
      </a>
    </li>
  );
}

function TenderRow({ t, hintCount, hintCats }: { t: TenderView; hintCount: number; hintCats: string[] }) {
  const badges: BadgeT[] = [
    ...(hintCount ? [{ код: 'match' as const, текст: `есть в ассортименте: ${hintCount}`, почему: hintCats.join(', ') }] : []),
    ...t.бейджи,
  ];
  return (
    <li className="tender-row">
      <div className="tr-main">
        <a className="tr-title" href={href(`/demo/tender/${t.key}`)}>{t.предмет}</a>
        <div className="tr-meta">{t.заказчик} · {t.регион}</div>
        <div className="badges">{badges.map((b, i) => <Badge key={b.код + i} b={b} />)}</div>
      </div>
      <dl className="tr-side">
        <div><dt>НМЦ</dt><dd>{rubShort(t.нмц)}</dd></div>
        <div><dt>{t.закон}</dt><dd>{t.способ}</dd></div>
        <div><dt>Окончание</dt><dd>{t.дата_окончания}</dd></div>
        <div><dt>Итог</dt><dd>{t.участников ? `${num(t.участников)} уч.` : '—'}{t['снижение_%'] !== null ? (t['снижение_%'] < 0.5 ? ', без снижения' : `, −${pct(t['снижение_%'], t['снижение_%'] < 10 ? 1 : 0)}`) : ''}</dd></div>
      </dl>
    </li>
  );
}
