import { useMemo, useState } from 'react';
import { DemoMark, Frame, SectionHead, Status } from '../../components/ui';
import { getTenderView, sverkaViews, tenderViews } from '../../data';
import { buildDraft, downloadCsv, downloadDocx, safeName } from '../../lib/draft';
import { expectedParticipants, lookupPrice, proposal } from '../../lib/price';
import { rub } from '../../lib/format';
import { go, href } from '../../router';
import { useApp } from '../../state';

export function TenderPicker({ current, base }: { current?: string; base: string }) {
  return (
    <label className="picker">Закупка
      <select value={current} onChange={(e) => go(`${base}/${e.target.value}`)}>
        <optgroup label="Со сверкой техзадания">
          {sverkaViews.map((v) => <option key={v.key} value={v.key}>{v.предмет}</option>)}
        </optgroup>
        <optgroup label="Из выгрузки (без техзадания)">
          {tenderViews.slice(0, 60).map((v) => <option key={v.key} value={v.key}>{v.предмет.slice(0, 80)}</option>)}
        </optgroup>
      </select>
    </label>
  );
}

export default function Draft({ id }: { id?: string }) {
  const { catalog } = useApp();
  const t = getTenderView(id) || sverkaViews[0];
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const price = useMemo(() => {
    if (!t?.нмц) return null;
    const f = lookupPrice(t.ниша, t.закон, t.способ, expectedParticipants(t).n);
    return f ? proposal(t.нмц, f.row).mid : null;
  }, [t]);
  const m = useMemo(() => (t ? buildDraft(t, t.sverka, catalog, price) : null), [t, catalog, price]);
  if (!t || !m) return <p>Нет данных.</p>;
  const base = safeName(t.номер || t.предмет);

  async function docx() {
    setBusy(true); setErr('');
    try { await downloadDocx(m!, base); } catch (e) { setErr(e instanceof Error ? e.message : 'Не получилось собрать файл'); } finally { setBusy(false); }
  }

  return (
    <>
      <SectionHead n={4} kicker="Демо-кабинет · раздел 4 из 5" title="Черновик заявки" lead="Пакет документов собран из сверки и вашего прайса. Это черновик: вы проверяете, юрист смотрит шаблоны, руководитель подписывает." />
      <div className="draft-tools">
        <TenderPicker current={t.key} base="/demo/zayavka" />
        <div className="cta-row">
          <button type="button" className="btn btn-solid" onClick={docx} disabled={busy}>{busy ? 'Собираю…' : 'Скачать черновик (.docx)'}</button>
          <button type="button" className="btn" onClick={() => downloadCsv(m, base)} disabled={!m.rows.length}>Таблица характеристик (.csv)</button>
        </div>
      </div>
      {err && <p className="form-error" role="alert">{err}</p>}

      <p className="legal-warn"><DemoMark>шаблоны</DemoMark> Все тексты — шаблоны: <b>проверить юристом</b>. Не юридическая консультация. Формы заказчика (если он их дал) важнее наших.</p>

      <div className="draft-grid">
        <aside className="draft-pack">
          <h3>Состав пакета</h3>
          <ol className="pack-list">
            <li className={m.rows.length ? 'done' : 'todo'}>Предложение участника: таблица характеристик {m.rows.length ? `(${m.rows.length} поз.)` : '— нет сверки'}</li>
            {m.docs.map((d) => <li key={d.title} className="tpl">{d.title.replace(/^\d+\.\s*/, '')} <span className="tpl-mark">шаблон</span></li>)}
          </ol>
          <h3>Перед подачей</h3>
          <ul className="checklist">
            {[...m.warnings, ...m.checklist].map((c) => <li key={c}>{c}</li>)}
          </ul>
          <p><a href={href(`/demo/sroki/${t.key}`)}>Дальше: сроки и деньги →</a></p>
        </aside>

        <Frame className="paper-doc">
          <p className="doc-stamp">ЧЕРНОВИК · проверить юристом</p>
          <h2 className="doc-title">{m.title}</h2>
          <dl className="doc-meta">{m.zakupka.map((z) => <div key={z.label}><dt>{z.label}</dt><dd>{z.value}</dd></div>)}</dl>

          <h3>Предложение участника в отношении объекта закупки</h3>
          {m.rows.length ? (
            <div className="table-scroll" tabIndex={0} role="region" aria-label="Таблица характеристик">
              <table className="data-table doc-table">
                <thead><tr><th scope="col">№</th><th scope="col">Позиция / товар</th><th scope="col">Характеристика</th><th scope="col">Требование</th><th scope="col">Значение у товара</th></tr></thead>
                <tbody>
                  {m.rows.map((r) => r.характеристики.map((c, i) => (
                    <tr key={`${r.n}-${i}`} className={i === 0 ? 'first' : ''}>
                      {i === 0 && <td rowSpan={r.характеристики.length}>{r.n}</td>}
                      {i === 0 && (
                        <td rowSpan={r.характеристики.length}>
                          <b>{r.позиция}</b> ({r.количество})<br />{r.товар}<br /><span className="muted">Страна: {r.страна}</span><br /><Status s={r.статус as 'подходит'} />
                        </td>
                      )}
                      <td>{c.имя}</td>
                      <td>{c.требование}</td>
                      <td className={c.значение.includes('⚠') ? 'warn' : ''}>{c.значение}</td>
                    </tr>
                  )))}
                </tbody>
              </table>
            </div>
          ) : <p className="muted">Нет сверки техзадания — таблица будет заполнена после разбора документа.</p>}

          {m.docs.map((d) => (
            <section key={d.title} className="doc-part">
              <h3>{d.title} <span className="tpl-mark">шаблон — проверить юристом</span></h3>
              {d.text.map((p, i) => <p key={i}>{p}</p>)}
              <p className="sign">__________ (должность, ФИО) ____________ (подпись)</p>
            </section>
          ))}
          {price && <p className="muted">Цена в черновике — медиана по похожим закупкам: {rub(price)}. Свою цену вы выбираете в карточке тендера.</p>}
        </Frame>
      </div>
    </>
  );
}
