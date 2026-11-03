import { useState, type ReactNode } from 'react';
import { Emblem, ScaleSwitch } from '../../components/ui';
import { getMode, liveAvailable, setMode, type AiMode } from '../../ai';
import { firstSverkaKey } from '../../data';
import { roman } from '../../lib/format';
import { href } from '../../router';
import { useApp } from '../../state';

export type Section = 'assortiment' | 'tendery' | 'tender' | 'zayavka' | 'sroki';

const NAV: { key: Section; title: string; short: string; to: (id?: string) => string }[] = [
  { key: 'assortiment', title: 'Ваш ассортимент', short: 'Ассортимент', to: () => '/demo/assortiment' },
  { key: 'tendery', title: 'Подходящие тендеры', short: 'Тендеры', to: () => '/demo/tendery' },
  { key: 'tender', title: 'Карточка тендера', short: 'Карточка', to: (id) => `/demo/tender/${id || firstSverkaKey}` },
  { key: 'zayavka', title: 'Черновик заявки', short: 'Заявка', to: (id) => `/demo/zayavka/${id || firstSverkaKey}` },
  { key: 'sroki', title: 'Сроки и деньги', short: 'Сроки', to: (id) => `/demo/sroki/${id || firstSverkaKey}` },
];

export function AiModeSwitch() {
  const [mode, setM] = useState<AiMode>(getMode());
  const live = liveAvailable();
  if (!live) {
    return (
      <div className="ai-mode" title="Ключ Claude API не задан: разбор работает по правилам и на подготовленных примерах">
        <span className="ai-dot" aria-hidden="true" /> ИИ: демо-режим, без ключа
      </div>
    );
  }
  return (
    <div className="ai-mode live" role="group" aria-label="Режим ИИ">
      <button type="button" aria-pressed={mode === 'демо'} className={mode === 'демо' ? 'on' : ''} onClick={() => { setMode('демо'); setM('демо'); }}>Демо</button>
      <button type="button" aria-pressed={mode === 'живой'} className={mode === 'живой' ? 'on' : ''} onClick={() => { setMode('живой'); setM('живой'); }}>Живой (Claude)</button>
      {mode === 'живой' && <span className="ai-warn">Ключ в браузере — только для локального теста</span>}
    </div>
  );
}

export default function CabinetLayout({ section, tenderId, children }: { section: Section; tenderId?: string; children: ReactNode }) {
  const { catalog, isSample } = useApp();
  return (
    <div className="cabinet">
      <a className="skip" href="#cab-main" onClick={(e) => { e.preventDefault(); document.getElementById('cab-main')?.focus(); }}>К содержанию</a>
      <header className="cab-top">
        <div className="cab-top-row">
          <a className="cab-brand" href={href('/')} aria-label="На главную страницу">
            <Emblem size={36} />
            <span><strong>Тендер под ключ</strong><small>демо-кабинет поставщика</small></span>
          </a>
          <div className="cab-tools">
            <AiModeSwitch />
            <ScaleSwitch />
          </div>
        </div>
        <div className="demo-banner" role="note">
          <strong>ДЕМО.</strong> Поставщик «Пример-Оргтехника» — вымышленный. Закупки и их извещения реальные; каталог, сверка и расчёты — демонстрационные.
          {' '}Ассортимент: {catalog.length} поз. {isSample ? '(демо-каталог)' : '(ваш файл)'}.
        </div>
      </header>
      <div className="cab-body">
        <nav className="cab-nav" aria-label="Разделы кабинета">
          <ol>
            {NAV.map((n, i) => (
              <li key={n.key}>
                <a href={href(n.to(tenderId))} aria-current={section === n.key ? 'page' : undefined} className={section === n.key ? 'on' : ''}>
                  <span className="roman-sm">{roman(i + 1)}.</span> <span className="nav-long">{n.title}</span><span className="nav-short">{n.short}</span>
                </a>
              </li>
            ))}
          </ol>
        </nav>
        <main id="cab-main" className="cab-main" tabIndex={-1}>{children}</main>
      </div>
      <footer className="cab-footer">
        Прототип. Все результаты — демо. Документы — шаблоны, проверить юристом. Не юридическая консультация.
      </footer>
    </div>
  );
}
