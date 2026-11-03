// Раздел «Статьи для поставщиков» (блок L): список, страница статьи, частые вопросы.
// Markdown превращается в HTML при сборке (scripts/sync_external.mjs, библиотека marked),
// поэтому на странице нет разбора и всё работает из одного файла без сервера.
// Ссылки #pilot в статьях ведут на форму «Хочу пилот» на лендинге (маршрут #/pilot).

import { useState } from 'react';
import { DemoMark, Emblem, Fleuron, Frame, Kicker, ScaleSwitch } from '../components/ui';
import { articles, faq, type ArticleData } from '../data';
import { href } from '../router';

const MONTHS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];
function ruDate(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  return m ? `${Number(m[3])} ${MONTHS[Number(m[2]) - 1]} ${m[1]}` : iso;
}
const minutes = (a: ArticleData) => Math.max(1, Math.round(a.слов / 180));

export function PublicHeader({ here }: { here: 'stati' | 'voprosy' }) {
  return (
    <header className="masthead">
      <div className="wrap">
        <nav className="mast-nav" aria-label="Главное меню">
          <div className="mast-side">
            <a className="mast-link" href={href('/')}>Главная</a>
            <a className="mast-link" href={href('/stati')} aria-current={here === 'stati' ? 'page' : undefined}>Статьи</a>
          </div>
          <a className="mast-center" href={href('/')} aria-label="Тендер под ключ — на главную"><Emblem size={52} /></a>
          <div className="mast-side right">
            <a className="mast-link" href={href('/voprosy')} aria-current={here === 'voprosy' ? 'page' : undefined}>Вопросы</a>
            <a className="mast-link" href={href('/demo/assortiment')}>Кабинет</a>
          </div>
        </nav>
        <div className="mast-tools"><ScaleSwitch /></div>
      </div>
      <div className="oxford" aria-hidden="true" />
    </header>
  );
}

function PublicFooter() {
  return (
    <footer className="site-footer">
      <div className="oxford" aria-hidden="true" />
      <div className="wrap footer-grid">
        <div>
          <div className="footer-brand"><Emblem size={36} /> <span>Тендер под ключ</span></div>
          <p>Прототип, ноябрь 2026. Материалы сайта — не юридическая консультация.</p>
        </div>
        <div>
          <p>Нормы в статьях сверены по текстам законов на consultant.ru на 3–4 ноября 2026 года. Акты меняются часто: перед подачей заявки сверяйте актуальную редакцию.</p>
        </div>
        <div><a className="btn btn-solid" href={href('/pilot')}>Хочу пилот</a></div>
      </div>
    </footer>
  );
}

function PilotCta() {
  return (
    <Frame ornate className="article-cta">
      <Kicker>Следующий шаг</Kicker>
      <h3>Проверим один ваш тендер бесплатно</h3>
      <p>Первый тендер на пилоте мы проводим под ключ без оплаты. Оставьте контакты, договоримся.</p>
      <div className="cta-row">
        <a className="btn btn-solid" href={href('/pilot')}>Хочу пилот</a>
        <a className="btn" href={href('/demo/assortiment')}>Посмотреть демо-кабинет</a>
      </div>
    </Frame>
  );
}

export function ArticleList() {
  return (
    <div className="landing public">
      <PublicHeader here="stati" />
      <main id="main" className="wrap article-wrap">
        <Kicker>Раздел для поставщиков</Kicker>
        <h1 className="page-title">Статьи для поставщиков</h1>
        <p className="lead page-lead">Короткие разборы по тому, что чаще всего ломает заявку: нацрежим, цена, гарантия, подпись, «или эквивалент». Простым языком, с источниками.</p>
        <p className="muted-note"><DemoMark>черновик</DemoMark> Тексты подготовлены для пилота и перед публикацией проходят проверку юриста. Не юридическая консультация.</p>

        <ol className="article-list">
          {articles.map((a, i) => (
            <li key={a.slug}>
              <a className="article-card" href={href(`/stati/${a.slug}`)}>
                <span className="ac-num" aria-hidden="true">{i + 1}</span>
                <span className="ac-body">
                  <span className="ac-title">{a.заголовок}</span>
                  <span className="ac-desc">{a.description}</span>
                  <span className="ac-meta">{ruDate(a.date)} · около {minutes(a)} мин чтения</span>
                </span>
              </a>
            </li>
          ))}
        </ol>

        <a className="faq-banner" href={href('/voprosy')}>
          <span className="ac-title">Частые вопросы: {faq.reduce((s, g) => s + g.вопросы.length, 0)} коротких ответов</span>
          <span className="ac-desc">Нацрежим, цена, гарантия, 223-ФЗ, отклонение заявки, подпись, оргтехника, «или эквивалент».</span>
        </a>
        <Fleuron />
        <PilotCta />
      </main>
      <PublicFooter />
    </div>
  );
}

export function ArticlePage({ slug }: { slug?: string }) {
  const idx = articles.findIndex((a) => a.slug === slug);
  const a = articles[idx];
  if (!a) {
    return (
      <div className="landing public">
        <PublicHeader here="stati" />
        <main id="main" className="wrap article-wrap">
          <h1 className="page-title">Такой статьи нет</h1>
          <p><a href={href('/stati')}>← Все статьи</a></p>
        </main>
        <PublicFooter />
      </div>
    );
  }
  const prev = articles[idx - 1], next = articles[idx + 1];
  return (
    <div className="landing public">
      <PublicHeader here="stati" />
      <main id="main" className="wrap article-wrap">
        <p className="crumbs"><a href={href('/stati')}>← Все статьи</a></p>
        <article className="article">
          <Kicker>Статья {idx + 1} из {articles.length} · {ruDate(a.date)} · около {minutes(a)} мин</Kicker>
          <h1 className="page-title">{a.заголовок}</h1>
          <p className="lead page-lead">{a.description}</p>
          <div className="prose" dangerouslySetInnerHTML={{ __html: a.html }} />
          {a.tags.length > 0 && <ul className="tags" aria-label="Темы">{a.tags.map((t) => <li key={t}>{t}</li>)}</ul>}
        </article>
        <PilotCta />
        <nav className="article-nav" aria-label="Другие статьи">
          {prev ? <a href={href(`/stati/${prev.slug}`)}><span className="muted">← Предыдущая</span><b>{prev.заголовок}</b></a> : <span />}
          {next ? <a className="next" href={href(`/stati/${next.slug}`)}><span className="muted">Следующая →</span><b>{next.заголовок}</b></a> : <span />}
        </nav>
        <p className="crumbs"><a href={href('/voprosy')}>Частые вопросы →</a></p>
      </main>
      <PublicFooter />
    </div>
  );
}

export function FaqPage() {
  const [openAll, setOpenAll] = useState(false);
  const total = faq.reduce((s, g) => s + g.вопросы.length, 0);
  let n = 0;
  return (
    <div className="landing public">
      <PublicHeader here="voprosy" />
      <main id="main" className="wrap article-wrap">
        <Kicker>Раздел для поставщиков</Kicker>
        <h1 className="page-title">Частые вопросы</h1>
        <p className="lead page-lead">{total} коротких ответов поставщика: нацрежим, закупка «под своего», цена, гарантия, 223-ФЗ, отклонение заявки, подпись, оргтехника.</p>
        <p className="muted-note"><DemoMark>черновик</DemoMark> Не юридическая консультация. Ответы основаны на текстах законов с consultant.ru на 3–4 ноября 2026 года; подробности — в <a href={href('/stati')}>статьях</a>.</p>
        <div className="cta-row"><button type="button" className="btn btn-small" onClick={() => setOpenAll(!openAll)}>{openAll ? 'Свернуть все' : 'Раскрыть все'}</button></div>
        {faq.map((g) => (
          <section key={g.тема} className="faq-group" aria-labelledby={`faq-${g.тема}`}>
            <h2 id={`faq-${g.тема}`} className="h3-rule">{g.тема}</h2>
            {g.вопросы.map((q) => {
              n += 1;
              return (
                <details key={q.вопрос} className="faq-item" open={openAll || undefined}>
                  <summary><span className="faq-n">{n}.</span> {q.вопрос}</summary>
                  <div className="prose" dangerouslySetInnerHTML={{ __html: q.ответ }} />
                </details>
              );
            })}
          </section>
        ))}
        <Fleuron />
        <PilotCta />
      </main>
      <PublicFooter />
    </div>
  );
}
