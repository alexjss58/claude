import { useState, type FormEvent } from 'react';
import { DemoMark, Emblem, Fleuron, Frame, Kicker, ScaleSwitch, SectionHead, SourceNote } from '../components/ui';
import { firstSverkaKey, market, SOURCE_NOTE, tendersMeta } from '../data';
import { num, pct, roman } from '../lib/format';
import { href } from '../router';

const scrollTo = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });

const CONTENTS: [string, string][] = [
  ['dlya-kogo', 'Для кого'],
  ['kak', 'Как работает: пять шагов'],
  ['pochemu', 'Почему не Контур и не Тендерплан'],
  ['rynok', 'Цифры рынка'],
  ['usloviya', 'Условия пилота'],
  ['pilot', 'Заявка на пилот'],
];

const STEPS = [
  { t: 'Поиск', we: 'Каждый день просматриваем новые закупки по вашим кодам и словам. Отсеиваем монтаж, ремонт и услуги, отмечаем закупки «под своего».', you: 'Нажимаете «беру» или «пропускаю».', demo: '/demo/tendery' },
  { t: 'Сверка техзадания с вашим ассортиментом', we: 'Читаем техническое задание и сравниваем каждую позицию с вашим прайсом: зелёный — подходит, жёлтый — почти (показываем, что мешает), красный — товара нет.', you: 'Решаете по жёлтым позициям.', demo: `/demo/tender/${firstSverkaKey}` },
  { t: 'Цена', we: 'Показываем, как падала цена в похожих закупках и у этого заказчика. Предлагаем диапазон и считаем вашу маржу.', you: 'Выбираете цену.', demo: `/demo/tender/${firstSverkaKey}` },
  { t: 'Заявка и документы', we: 'Собираем таблицу характеристик, декларации, сведения о стране происхождения для нацрежима.', you: 'Проверяете и подписываете электронной подписью.', demo: `/demo/zayavka/${firstSverkaKey}` },
  { t: 'Гарантия и сроки', we: 'Ведём сроки: итоги, подписание, обеспечение или банковская гарантия, поставка, приёмка, оплата. Считаем, сколько денег и на сколько дней нужно.', you: 'Поставляете товар.', demo: `/demo/sroki/${firstSverkaKey}` },
];

export default function Landing() {
  return (
    <div className="landing">
      <a className="skip" href="#main" onClick={(e) => { e.preventDefault(); scrollTo('main'); }}>К содержанию</a>
      <header className="masthead">
        <div className="wrap">
          <div className="dateline">
            <span>Выпуск пилотный · ноябрь 2026</span>
            <span className="hide-sm">Для поставщиков оргтехники, связи и приборов</span>
            <span>Цена номера: первый тендер бесплатно</span>
          </div>
          <nav className="mast-nav" aria-label="Главное меню">
            <div className="mast-side">
              <button type="button" className="mast-link" onClick={() => scrollTo('kak')}>Как работает</button>
              <button type="button" className="mast-link hide-sm" onClick={() => scrollTo('rynok')}>Рынок</button>
            </div>
            <a className="mast-center" href={href('/')} aria-label="Тендер под ключ — на главную">
              <Emblem size={52} />
            </a>
            <div className="mast-side right">
              <button type="button" className="mast-link hide-sm" onClick={() => scrollTo('usloviya')}>Условия</button>
              <a className="mast-link" href={href('/demo/assortiment')}>Демо-кабинет</a>
            </div>
          </nav>
          <div className="mast-tools"><ScaleSwitch /></div>
        </div>
        <div className="oxford" aria-hidden="true" />
      </header>

      <main id="main">
        <section className="hero wrap">
          <Kicker>Тендеры по 44-ФЗ, 223-ФЗ и коммерческие</Kicker>
          <h1 className="hero-title">Тендер под&nbsp;ключ</h1>
          <div className="hero-grid">
            <div className="hero-copy">
              <p className="hero-lead dropcap">
                ИИ снимает 80–90% рутины поставщика в тендерах. Вам остаётся подтвердить, подписать заявку и поставить товар.
              </p>
              <p>
                Мы находим закупки, сверяем техническое задание с вашим каталогом, считаем цену, собираем заявку и документы,
                ведём сроки и банковскую гарантию. Мы не «разбираем тендеры» — мы закрываем ваш вопрос с тендером.
              </p>
              <div className="cta-row">
                <a className="btn btn-solid" href={href('/demo/assortiment')}>Открыть демо-кабинет</a>
                <button type="button" className="btn" onClick={() => scrollTo('pilot')}>Хочу пилот</button>
              </div>
            </div>
            <aside className="hero-aside">
              <Frame ornate className="contents">
                <div className="contents-title">Содержание номера</div>
                <ol>
                  {CONTENTS.map(([id, t], i) => (
                    <li key={id}>
                      <button type="button" onClick={() => scrollTo(id)}>
                        <span className="roman-sm">{roman(i + 1)}.</span>
                        <span className="dots">{t}</span>
                      </button>
                    </li>
                  ))}
                </ol>
              </Frame>
              <div className="plate" role="note">
                <div className="plate-inner">
                  <span className="plate-kicker">Цель пилота</span>
                  <strong>+10 заявок в месяц</strong>
                  <span>без найма нового сотрудника</span>
                </div>
              </div>
            </aside>
          </div>
        </section>

        <Fleuron />

        <section id="dlya-kogo" className="wrap section">
          <SectionHead n={1} kicker="Для кого" title="Поставщикам без большого тендерного отдела" lead="Тем, у кого тендерами занимается руководитель или один менеджер — по вечерам и между другими делами." />
          <div className="cards3">
            <Frame className="card"><h3>Подаёте сами</h3><p>2–5 заявок в месяц, остальные закупки пропускаете: не хватает времени прочитать техзадание.</p></Frame>
            <Frame className="card"><h3>Есть свой тендерщик</h3><p>Он не успевает: на одну заявку уходит день, а подходящих закупок — десятки в неделю.</p></Frame>
            <Frame className="card"><h3>Уже выигрываете</h3><p>Когда участвуете — побеждаете. Хотите подавать больше заявок, не нанимая людей.</p></Frame>
          </div>
          <Frame ornate className="insight">
            <div className="insight-text">
              <Kicker>Что видно в данных</Kicker>
              <h3>Лидеры ниш выигрывают почти всё, где участвуют</h3>
              <p>Значит, узкое место не в шансе на победу, а в том, сколько заявок вы успеваете подать. Поэтому мы продаём объём: больше поданных заявок теми же силами.</p>
            </div>
            <div className="leaders">
              {market.лидеры?.map((l) => (
                <table key={l.код} className="mini-table">
                  <caption>{l.код === 'svyaz' ? 'Связь и аудио-видео' : 'Приборы'}: топ-5 за квартал</caption>
                  <thead><tr><th scope="col">Поставщик</th><th scope="col">Участий</th><th scope="col">Побед</th></tr></thead>
                  <tbody>
                    {l.поставщики.map((p) => (
                      <tr key={p.место}><td>№ {p.место}</td><td>{p.участий}</td><td>{p.побед}</td></tr>
                    ))}
                  </tbody>
                </table>
              ))}
            </div>
            <SourceNote>{SOURCE_NOTE}. Лист «Подрядчики», квартал; названия компаний скрыты.</SourceNote>
          </Frame>
        </section>

        <Fleuron />

        <section id="kak" className="wrap section">
          <SectionHead n={2} kicker="Как работает" title="Пять шагов от закупки до оплаты" lead="Программа берёт на себя чтение, сверку и сборку документов. Решения и подпись остаются за вами." />
          <ol className="steps">
            {STEPS.map((s, i) => (
              <li key={s.t} className="step">
                <div className="step-num" aria-hidden="true">{i + 1}</div>
                <div className="step-body">
                  <h3>{s.t}</h3>
                  <p><span className="who">Мы:</span> {s.we}</p>
                  <p><span className="who">Вы:</span> {s.you}</p>
                  <a className="link-arrow" href={href(s.demo)}>Посмотреть в демо</a>
                </div>
              </li>
            ))}
          </ol>
        </section>

        <Fleuron />

        <section id="pochemu" className="wrap section">
          <SectionHead n={3} kicker="Чем отличаемся" title="Почему не Контур и не Тендерплан" lead="Это хорошие сервисы, мы их не заменяем. Поиск закупок у них есть. Мы делаем работу, которая начинается после поиска." />
          <div className="three-points">
            <div><div className="big-word">Часы</div><p>вместо дней на одну заявку. Это цель пилота: замерим на ваших тендерах.</p></div>
            <div><div className="big-word">Ваш каталог</div><p>Сверяем техзадание с вашим прайсом позиция за позицией, а не просто ищем по словам.</p></div>
            <div><div className="big-word">Больше заявок</div><p>без найма тендерного специалиста. Платите за поданные заявки и за победы.</p></div>
          </div>
          <div className="table-scroll" tabIndex={0} role="region" aria-label="Сравнение подходов">
            <table className="compare">
              <thead>
                <tr><th scope="col"></th><th scope="col">Сервис поиска закупок</th><th scope="col">Сопровождение тендеров</th><th scope="col" className="ours">Тендер под ключ</th></tr>
              </thead>
              <tbody>
                <tr><th scope="row">Что получаете</th><td>Список закупок по фильтрам</td><td>Специалист готовит заявку</td><td className="ours">Готовый пакет: от поиска до гарантии</td></tr>
                <tr><th scope="row">Подходит ли ваш товар</th><td>Решаете сами, читая техзадание</td><td>Специалист проверяет вручную</td><td className="ours">Сверка с вашим прайсом по каждой позиции</td></tr>
                <tr><th scope="row">Цена</th><td>Аналитика по рынку</td><td>По опыту специалиста</td><td className="ours">Диапазон по истории ниши и заказчика + ваша маржа</td></tr>
                <tr><th scope="row">Чтобы подавать больше</th><td>Нужно больше людей</td><td>Больше платежей за заявки</td><td className="ours">Те же люди, больше заявок</td></tr>
              </tbody>
            </table>
          </div>
          <SourceNote>Сравниваем подходы, а не тарифы конкретных компаний. Наши преимущества — гипотезы, которые проверяем на пилоте.</SourceNote>
        </section>

        <Fleuron />

        <section id="rynok" className="wrap section">
          <SectionHead n={4} kicker="Цифры рынка" title="Две ниши пилота за три месяца" lead={`Завершённые закупки по 44-ФЗ и 223-ФЗ, ${market.ниши[0]?.период?.replace('С ', 'с ') || ''}.`} />
          <div className="market">
            {market.ниши.map((m) => (
              <Frame key={m.код} className="market-col">
                <h3>{m.название}</h3>
                <dl className="stats">
                  <div><dt>Закупок</dt><dd>{num(m.закупок_за_период)}</dd></div>
                  <div><dt>На сумму</dt><dd>{m.сумма_за_период}</dd></div>
                  <div><dt>Среднее снижение цены</dt><dd>{pct(m['среднее_снижение_%'])}</dd></div>
                  <div><dt>Участников в среднем</dt><dd>{num(m.среднее_участников, 1)}</dd></div>
                  <div><dt>С одним участником*</dt><dd>{pct(m['доля_с_одним_участником_%_выгрузка'], 0)}</dd></div>
                  <div><dt>Чистая поставка*</dt><dd>{pct(m['доля_чистой_поставки_%_выгрузка'], 0)}</dd></div>
                </dl>
              </Frame>
            ))}
          </div>
          <SourceNote>
            {SOURCE_NOTE}. Первые четыре строки — сводка Тендерплана по выборке (лист «Анализ»).
            * — наш расчёт по строкам выгрузки ({num(Number(tendersMeta.всего_строк))} закупок после удаления дублей):
            доля закупок с одним участником и доля «чистой поставки» без монтажа, ремонта и услуг (правила по названию закупки).
          </SourceNote>
        </section>

        <Fleuron />

        <section id="usloviya" className="wrap section">
          <SectionHead n={5} kicker="Пилотные условия, гипотеза" title="Сколько стоит" lead="Условия пилота — гипотеза. Точные суммы обсуждаем на созвоне и уточняем по итогам первых тендеров." />
          <div className="price-cards">
            <Frame ornate className="price-card featured"><div className="price-big">0 ₽</div><h3>Первый тендер</h3><p>Проводим под ключ бесплатно. Взамен — 20–30 минут разговора о том, как у вас устроена работа с тендерами.</p></Frame>
            <Frame className="price-card"><div className="price-big">за заявку</div><h3>Дальше — оплата за поданную заявку</h3><p>Платите только за заявки, которые подали. Нет заявки — нет оплаты.</p></Frame>
            <Frame className="price-card"><div className="price-big">+ % с победы</div><h3>Небольшой процент, если выиграли</h3><p>Нам выгодно, чтобы вы побеждали с хорошей маржой, а не просто подавали больше.</p></Frame>
          </div>
          <p className="muted-note"><DemoMark>пилотные условия</DemoMark> Это не публичная оферта. От вас на пилоте: прайс в Excel и сотрудник с электронной подписью. Доступ к площадке — только по вашему решению.</p>
        </section>

        <Fleuron />

        <section id="pilot" className="wrap section">
          <SectionHead n={6} kicker="Заявка на пилот" title="Хочу пилот" lead="Оставьте контакты — договоримся о первом бесплатном тендере." />
          <PilotForm />
        </section>
      </main>

      <footer className="site-footer">
        <div className="oxford" aria-hidden="true" />
        <div className="wrap footer-grid">
          <div>
            <div className="footer-brand"><Emblem size={36} /> <span>Тендер под ключ</span></div>
            <p>Прототип, ноябрь 2026. Демо-данные помечены. Материалы сайта — не юридическая консультация.</p>
          </div>
          <div>
            <p>Цифры рынка: {SOURCE_NOTE}.</p>
            <p>Шрифты: Old Standard TT, PT Serif, IBM Plex Sans и IBM Plex Mono (свободная лицензия SIL OFL).</p>
          </div>
          <div>
            <a className="btn btn-solid" href={href('/demo/assortiment')}>Демо-кабинет</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

const PILOT_KEY = 'tpk_pilot_requests';

function PilotForm() {
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const onSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const data = Object.fromEntries(fd.entries());
    if (!String(data.name || '').trim() || !String(data.contact || '').trim()) {
      setError('Укажите имя и телефон или почту — иначе мы не сможем ответить.');
      return;
    }
    // ПРОТОТИП: заявка сохраняется только в этом браузере (localStorage) и никуда не отправляется.
    // Чтобы получать заявки по-настоящему, здесь нужно отправить data на свой сервер или в сервис форм,
    // например: await fetch('https://<ваш-сервер>/api/pilot', { method: 'POST', body: JSON.stringify(data) }).
    // Перед этим — добавить согласие на обработку персональных данных (152-ФЗ) и политику конфиденциальности.
    try {
      const list = JSON.parse(localStorage.getItem(PILOT_KEY) || '[]');
      list.push({ ...data, at: new Date().toISOString() });
      localStorage.setItem(PILOT_KEY, JSON.stringify(list));
    } catch { /* хранилище недоступно — всё равно показываем «спасибо» */ }
    setError('');
    setSent(true);
  };
  if (sent) {
    return (
      <Frame ornate className="pilot-form thanks" role="status" aria-live="polite">
        <h3>Спасибо!</h3>
        <p>Заявка сохранена. Это прототип: данные остались в вашем браузере и никуда не отправлены. В рабочей версии мы ответим в течение дня.</p>
        <button type="button" className="btn" onClick={() => setSent(false)}>Заполнить ещё раз</button>
      </Frame>
    );
  }
  return (
    <Frame ornate as="form" className="pilot-form" onSubmit={onSubmit} noValidate>
      <p className="form-note"><DemoMark>прототип</DemoMark> Данные никуда не отправляются: сохраняются только в вашем браузере.</p>
      <div className="form-grid">
        <label>Имя<input name="name" autoComplete="name" required /></label>
        <label>Компания<input name="company" autoComplete="organization" /></label>
        <label>Телефон или почта<input name="contact" autoComplete="email" required /></label>
        <label>Что поставляете
          <select name="niche" defaultValue="Оргтехника">
            <option>Оргтехника</option>
            <option>Связь и аудио-видеотехника</option>
            <option>Измерительные и лабораторные приборы</option>
            <option>Лабораторные реактивы</option>
            <option>Другое</option>
          </select>
        </label>
        <label>Сколько заявок в месяц подаёте сейчас
          <select name="volume" defaultValue="1–5">
            <option>0</option><option>1–5</option><option>6–15</option><option>16–30</option><option>больше 30</option>
          </select>
        </label>
        <label className="span2">Комментарий<textarea name="comment" rows={3} placeholder="Например: какие закупки хотите подавать" /></label>
      </div>
      {error && <p className="form-error" role="alert">{error}</p>}
      <button type="submit" className="btn btn-solid">Отправить заявку</button>
    </Frame>
  );
}
