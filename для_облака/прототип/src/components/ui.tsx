// Общие элементы интерфейса: орнаменты (свои, нарисованы с нуля), метки, бейджи, статусы.

import type { ReactNode } from 'react';
import type { Badge as BadgeT, СтатусСверки } from '../types';
import { roman } from '../lib/format';
import { useApp } from '../state';

/** Концовка-флерон между разделами: ромб, точки и два завитка. Свой рисунок. */
export function Fleuron({ className = '' }: { className?: string }) {
  return (
    <div className={`fleuron ${className}`} aria-hidden="true">
      <span className="fleuron-line" />
      <svg viewBox="0 0 120 24" width="120" height="24">
        <path d="M60 3 L67 12 L60 21 L53 12 Z" fill="currentColor" />
        <circle cx="44" cy="12" r="2.2" fill="currentColor" />
        <circle cx="76" cy="12" r="2.2" fill="currentColor" />
        <path d="M40 12 C 32 2, 18 2, 14 10 C 12 15, 20 17, 22 12" fill="none" stroke="currentColor" strokeWidth="1.6" />
        <path d="M80 12 C 88 2, 102 2, 106 10 C 108 15, 100 17, 98 12" fill="none" stroke="currentColor" strokeWidth="1.6" />
      </svg>
      <span className="fleuron-line" />
    </div>
  );
}

/** Эмблема «ТК» в двойной рамке — своя, не похожа ни на чей знак */
export function Emblem({ size = 56 }: { size?: number }) {
  return (
    <svg className="emblem" viewBox="0 0 64 64" width={size} height={size} aria-hidden="true">
      <rect x="1.5" y="1.5" width="61" height="61" fill="var(--paper)" stroke="currentColor" strokeWidth="3" />
      <rect x="7" y="7" width="50" height="50" fill="none" stroke="currentColor" strokeWidth="1" />
      <path d="M7 15 L15 7 M49 7 L57 15 M57 49 L49 57 M15 57 L7 49" stroke="currentColor" strokeWidth="1" />
      <text x="32" y="41" textAnchor="middle" fontFamily="'Old Standard TT', serif" fontWeight="700" fontSize="24" fill="var(--accent)">ТК</text>
    </svg>
  );
}

/** Уголки для журнальной рамки */
export function Corners() {
  const c = <svg viewBox="0 0 16 16" width="16" height="16"><path d="M1 15 V1 H15" fill="none" stroke="currentColor" strokeWidth="2" /><rect x="4" y="4" width="4" height="4" fill="currentColor" /></svg>;
  return (
    <span className="corners" aria-hidden="true">
      <span className="corner tl">{c}</span><span className="corner tr">{c}</span>
      <span className="corner bl">{c}</span><span className="corner br">{c}</span>
    </span>
  );
}

export function Frame({ children, className = '', ornate = false, as: Tag = 'div', ...rest }: { children: ReactNode; className?: string; ornate?: boolean; as?: 'div' | 'section' | 'aside' | 'form'; [k: string]: unknown }) {
  return (
    <Tag className={`frame ${ornate ? 'frame-ornate' : ''} ${className}`} {...rest}>
      {ornate && <Corners />}
      {children}
    </Tag>
  );
}

export function Kicker({ children }: { children: ReactNode }) {
  return <div className="kicker">{children}</div>;
}

export function SectionHead({ n, kicker, title, lead }: { n?: number; kicker?: string; title: ReactNode; lead?: ReactNode }) {
  return (
    <header className="section-head">
      <div className="section-head-top">
        {n !== undefined && <span className="roman" aria-hidden="true">{roman(n)}.</span>}
        {kicker && <Kicker>{kicker}</Kicker>}
      </div>
      <h2>{title}</h2>
      {lead && <p className="lead">{lead}</p>}
    </header>
  );
}

/** Метка «демо» — ставим везде, где данные примерные */
export function DemoMark({ children = 'демо' }: { children?: ReactNode }) {
  return <span className="demo-mark">{children}</span>;
}

export function SourceNote({ children }: { children: ReactNode }) {
  return <p className="source-note">{children}</p>;
}

export function Badge({ b }: { b: BadgeT }) {
  return (
    <span className={`badge badge-${b.код}`} title={b.почему}>
      {b.код === 'svoy' && <span aria-hidden="true">?</span>}
      {b.код === 'natreg' && <span aria-hidden="true">РФ</span>}
      {b.код === 'match' && <span aria-hidden="true">✓</span>}
      {b.текст}
    </span>
  );
}

const STATUS_TEXT: Record<СтатусСверки, string> = { подходит: 'подходит', почти: 'почти', нет: 'нет товара' };

export function StatusIcon({ s }: { s: СтатусСверки }) {
  if (s === 'подходит') return <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M2.5 8.5 L6.5 12.5 L13.5 4" fill="none" stroke="currentColor" strokeWidth="2.4" /></svg>;
  if (s === 'почти') return <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M2 6 Q5 3.5 8 6 T14 6 M2 11 Q5 8.5 8 11 T14 11" fill="none" stroke="currentColor" strokeWidth="2" /></svg>;
  return <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M3.5 3.5 L12.5 12.5 M12.5 3.5 L3.5 12.5" fill="none" stroke="currentColor" strokeWidth="2.4" /></svg>;
}

export function Status({ s }: { s: СтатусСверки }) {
  return <span className={`status status-${s === 'подходит' ? 'ok' : s === 'почти' ? 'almost' : 'no'}`}><StatusIcon s={s} />{STATUS_TEXT[s]}</span>;
}

/** Переключатель крупного текста: А / А+ / А++ */
export function ScaleSwitch() {
  const { scale, setScale } = useApp();
  const opts: [number, string, string][] = [[1, 'А', 'Обычный текст'], [1.125, 'А+', 'Крупнее'], [1.25, 'А++', 'Самый крупный']];
  return (
    <div className="scale-switch" role="group" aria-label="Размер текста">
      {opts.map(([v, l, t]) => (
        <button key={v} type="button" className={scale === v ? 'on' : ''} aria-pressed={scale === v} title={t} onClick={() => setScale(v)}>{l}</button>
      ))}
    </div>
  );
}
