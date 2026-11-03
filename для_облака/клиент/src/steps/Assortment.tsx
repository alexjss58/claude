import { useRef, useState } from 'react';
import type { CatalogState } from '../state';
import type { Item } from '../types';
import type { ParsedSheet } from '../lib/catalog';
import { FIELD_LABELS, buildItems, loadFile, needsManual, parseCsvString, parseList } from '../lib/catalog';
import demoCsv from '../data/catalog_demo.csv?raw';
import { plural, rub } from '../lib/format';
import { Head } from './ui';

const PRIORITY = [/^процессор$/i, /^оперативная память/i, /^объ[её]м ssd/i, /^диагональ/i, /^скорость печати/i, /^порты 1g/i, /^полная мощность/i, /^световой поток/i, /^тип гарнитуры/i];
function specSummary(it: Item): string {
  const e = Object.entries(it.specs);
  if (!e.length) return '—';
  const pick: [string, string][] = [];
  for (const re of PRIORITY) { const f = e.find(([k]) => re.test(k.trim())); if (f && !pick.includes(f)) pick.push(f); if (pick.length === 2) break; }
  for (const f of e) { if (pick.length >= 2) break; if (!pick.includes(f)) pick.push(f); }
  const f = ([k, v]: [string, string]) => `${k.split(',')[0]}: ${v.length > 22 ? v.slice(0, 21) + '…' : v}`;
  return pick.map(f).join('; ') + (e.length > 2 ? ` · всего ${e.length}` : '');
}

export function Assortment({ value, onChange }: { value: CatalogState; onChange: (c: CatalogState) => void }) {
  const [text, setText] = useState(value.source === 'text' ? value.text : '');
  const [err, setErr] = useState('');
  const [over, setOver] = useState(false);
  const [sheet, setSheet] = useState<ParsedSheet | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const commit = (src: CatalogState['source'], name: string, items: Item[], raw = '') => {
    if (!items.length) { setErr('Не нашли ни одного товара. Проверьте файл или список.'); return; }
    setErr('');
    onChange({ source: src, name, text: raw, items });
  };

  const fromSheet = (p: ParsedSheet, src: 'file' | 'demo', name: string) => {
    if (needsManual(p)) { setSheet(p); setErr('Не поняли, где наименование. Укажите столбцы ниже.'); return; }
    setSheet(null);
    commit(src, name, buildItems(p));
  };

  const onFile = async (f: File | undefined | null) => {
    if (!f) return;
    setErr('');
    try { fromSheet(await loadFile(f), 'file', f.name); }
    catch (e) { setErr((e as Error).message || 'Не удалось прочитать файл.'); }
  };

  const setCol = (index: number, field: string) => {
    if (!sheet) return;
    const columns = sheet.columns.map((c) => (c.index === index ? { ...c, field: field as ParsedSheet['columns'][0]['field'] } : (field !== 'свойство' && field !== 'пропустить' && c.field === field ? { ...c, field: 'свойство' as const } : c)));
    const next = { ...sheet, columns };
    setSheet(next);
    if (!needsManual(next)) { setErr(''); commit('file', next.fileName, buildItems(next)); setSheet(null); }
  };

  const items = value.items;
  const hasPrice = items.some((i) => i.price != null);
  return (
    <div className="stack">
      <Head n="04" rubric="Ассортимент" title="Ваш ассортимент" lead="Нужно, чтобы сверить товары с тендерами. Файл остаётся в вашем браузере." />

      <div className={'drop' + (over ? ' over' : '')}
        onDragOver={(e) => { e.preventDefault(); setOver(true); }} onDragLeave={() => setOver(false)}
        onDrop={(e) => { e.preventDefault(); setOver(false); void onFile(e.dataTransfer.files?.[0]); }}>
        <p className="mono" style={{ marginBottom: 12 }}>Excel или CSV</p>
        <p style={{ marginBottom: 14 }}>Перетащите файл сюда или выберите на устройстве</p>
        <input ref={fileRef} type="file" className="sr" tabIndex={-1} accept=".xlsx,.csv,.txt,text/csv" onChange={(e) => { void onFile(e.target.files?.[0]); e.target.value = ''; }} />
        <button className="btn" type="button" onClick={() => fileRef.current?.click()}>Выбрать файл</button>
      </div>

      <div className="or mono dim">или</div>

      <div className="field">
        <label className="lbl mono" htmlFor="paste">Вставьте список, по товару на строку</label>
        <textarea id="paste" className="textarea" value={text} onChange={(e) => setText(e.target.value)} spellCheck={false}
          placeholder={'HP ProBook 450 G10 16/512 — 78 000\nCanon i-SENSYS MF445dw — 41 500'} />
        <div className="btnrow" style={{ marginTop: 10 }}>
          <button className="btn" type="button" disabled={!text.trim()} onClick={() => commit('text', 'список', parseList(text), text)}>Разобрать список</button>
        </div>
      </div>

      <div className="or mono dim">или</div>

      <button className="btn" type="button" onClick={() => { setText(''); fromSheet(parseCsvString('каталог_демо.csv', demoCsv), 'demo', 'пример'); }}>Нет файла — показать на примере</button>

      {err ? <p className="err" role="alert">{err}</p> : null}

      {sheet ? (
        <div className="field">
          <span className="lbl mono">Какой столбец что значит</span>
          {sheet.columns.filter((c) => c.field !== 'пропустить' || c.sample).slice(0, 12).map((c) => (
            <div key={c.index} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 8, alignItems: 'center' }}>
              <span style={{ overflowWrap: 'anywhere' }}>{c.header}<span className="hint" style={{ display: 'block', marginTop: 0 }}>{c.sample.slice(0, 28)}</span></span>
              <select className="select" aria-label={`Столбец ${c.header}`} value={c.field} onChange={(e) => setCol(c.index, e.target.value)}>
                {(['наименование', 'цена', 'производитель', 'модель', 'свойство', 'пропустить'] as const).map((f) => <option key={f} value={f}>{FIELD_LABELS[f]}</option>)}
              </select>
            </div>
          ))}
        </div>
      ) : null}

      {items.length > 0 ? (
        <div>
          <p className="got">Распознали <span className="num-hl">{items.length}</span> {plural(items.length, 'товар', 'товара', 'товаров')}
            {value.source === 'demo' ? <span className="tag dash" style={{ marginLeft: 10, verticalAlign: 'middle' }}>пример</span> : null}</p>
          {value.source !== 'demo' && items.every((i) => i.price == null) ? <p className="hint">Цен не нашли: себестоимость на последнем шаге введёте вручную.</p> : null}
          {value.source === 'text' ? <p className="hint">В списке нет характеристик: сверка будет «почти» и подскажет, что проверить.</p> : null}
          <table className="mini">
            <thead><tr><th>Наименование</th>{hasPrice ? <th className="r">Цена</th> : null}<th>Характеристики</th></tr></thead>
            <tbody>
              {items.slice(0, 5).map((it) => (
                <tr key={it.id}>
                  <td>{it.name}</td>
                  {hasPrice ? <td className="r">{it.price != null ? rub(it.price) : '—'}</td> : null}
                  <td className="dim">{specSummary(it)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
