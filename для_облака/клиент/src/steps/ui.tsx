import type { ReactNode } from 'react';

export function Rubric({ n, children }: { n?: string; children: ReactNode }) {
  return <div className="rubric mono">{n ? <span>{n}</span> : null}<span>{children}</span></div>;
}

export function Head({ n, rubric, title, lead }: { n: string; rubric: string; title: string; lead?: string }) {
  return (
    <header>
      <Rubric n={`Шаг ${n} / 06`}>{rubric}</Rubric>
      <h1 className="h1">{title}</h1>
      {lead ? <p className="lead">{lead}</p> : null}
    </header>
  );
}

export function Check({ on }: { on: boolean }) {
  return <span className={'box' + (on ? ' on' : '')} aria-hidden="true" />;
}
