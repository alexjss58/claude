import { useMemo, useRef, useState, type DragEvent } from 'react';
import { DemoMark, Frame, SectionHead } from '../../components/ui';
import { analyzeRows, buildCatalog, FIELD_LABELS, parseCsvText, readFileRows, type FieldKey, type ParsedSheet } from '../../lib/catalog';
import { engineCatalog, samplePriceCsv } from '../../data';
import { num, rub } from '../../lib/format';
import { href } from '../../router';
import { useApp } from '../../state';

const FIELDS = Object.keys(FIELD_LABELS) as FieldKey[];

export default function Assortment() {
  const { catalog, catalogSource, catalogKind, isSample, setCatalog, useBuiltin } = useApp();
  const [parsed, setParsed] = useState<ParsedSheet | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [drag, setDrag] = useState(false);
  const [saved, setSaved] = useState(false);
  const input = useRef<HTMLInputElement>(null);

  const preview = useMemo(() => (parsed ? buildCatalog(parsed) : null), [parsed]);

  async function onFile(f: File | undefined) {
    if (!f) return;
    setError(''); setSaved(false); setBusy(true);
    try {
      const { rows, notes } = await readFileRows(f);
      if (!rows.length) throw new Error('В файле не нашли строк с данными.');
      setParsed(analyzeRows(f.name, rows, notes));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось прочитать файл.');
      setParsed(null);
    } finally {
      setBusy(false);
    }
  }

  function useSample() {
    setError(''); setSaved(false);
    setParsed(analyzeRows('пример прайса оргтехники', parseCsvText(samplePriceCsv), ['Встроенный пример прайса: 47 позиций оргтехники, связи и аудио-видео, цены условные. Он отличается от демо-каталога, по которому сделаны сверки.']));
  }

  function setField(i: number, f: FieldKey) {
    if (!parsed) return;
    const columns = parsed.columns.map((c) => {
      if (c.index === i) return { ...c, field: f, confidence: 'точно' as const };
      if (f !== 'пропустить' && c.field === f) return { ...c, field: 'пропустить' as FieldKey, confidence: 'не найдено' as const };
      return c;
    });
    setParsed({ ...parsed, columns });
    setSaved(false);
  }

  function save() {
    if (!parsed || !preview) return;
    setCatalog(preview, parsed.fileName);
    setSaved(true);
  }

  const onDrop = (e: DragEvent) => { e.preventDefault(); setDrag(false); onFile(e.dataTransfer.files?.[0]); };
  const cats = useMemo(() => {
    const m = new Map<string, number>();
    for (const c of preview || catalog) m.set(c.категория, (m.get(c.категория) || 0) + 1);
    return [...m.entries()].sort((a, b) => b[1] - a[1]);
  }, [preview, catalog]);

  return (
    <>
      <SectionHead n={1} kicker="Демо-кабинет · раздел 1 из 5" title="Ваш ассортимент" lead="Загрузите прайс в Excel (.xlsx) или CSV. Мы найдём шапку таблицы, поймём, где наименование, цена и характеристики, и будем сверять с ним техзадания. Пока вы ничего не загрузили, в кабинете лежит демо-каталог: именно по нему сделаны сверки на реальных закупках." />

      <div className="assort-top">
        <div
          className={`dropzone ${drag ? 'drag' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
          onDragLeave={() => setDrag(false)}
          onDrop={onDrop}
        >
          <p className="dz-title">Перетащите файл сюда</p>
          <p>или</p>
          <div className="cta-row center">
            <button type="button" className="btn btn-solid" onClick={() => input.current?.click()} disabled={busy}>{busy ? 'Читаю файл…' : 'Выбрать файл'}</button>
            <button type="button" className="btn" onClick={useSample}>Разобрать пример прайса</button>
          </div>
          <input ref={input} type="file" accept=".xlsx,.csv,.txt" hidden onChange={(e) => { onFile(e.target.files?.[0]); e.target.value = ''; }} />
          <p className="dz-note">Файл обрабатывается в вашем браузере и никуда не отправляется.</p>
        </div>
        <Frame className="assort-current">
          <h3>Сейчас в кабинете</h3>
          <p className="big-num">{num(catalog.length)} <small>позиций</small></p>
          <p>Источник: {catalogSource} {isSample && <DemoMark>{catalogKind === 'движок' ? 'демо-каталог' : 'пример'}</DemoMark>}</p>
          {catalogKind === 'движок' && <p className="hint">Цен в демо-каталоге нет: производители их не публикуют. Себестоимость вы вводите сами в карточке тендера.</p>}
          <p className="downloads">Скачать для проверки: <a href="./katalog_demo.xlsx" download>демо-каталог движка, .xlsx</a> · пример прайса: <a href="./primer_praysa_orgtehniki.xlsx" download>.xlsx</a>, <a href="./primer_praysa_orgtehniki.csv" download>.csv</a></p>
          <div className="cta-row">
            {catalogKind !== 'движок' && engineCatalog.length > 0 && <button type="button" className="btn btn-small" onClick={() => useBuiltin('движок')}>Вернуть демо-каталог</button>}
            {catalogKind === 'движок' && <button type="button" className="btn btn-small" onClick={() => useBuiltin('пример')}>Заменить на пример прайса</button>}
            {catalogKind === 'свой' && <button type="button" className="btn btn-small" onClick={() => useBuiltin('пример')}>Заменить на пример прайса</button>}
          </div>
        </Frame>
      </div>

      {error && <p className="form-error" role="alert">{error}</p>}

      {parsed && preview && (
        <section className="parse-result" aria-live="polite">
          <h3 className="h3-rule">Разбор файла «{parsed.fileName}»</h3>
          {parsed.notes.length > 0 && <ul className="notes">{parsed.notes.map((n) => <li key={n}>{n}</li>)}</ul>}

          <h4>Столбцы: что мы поняли</h4>
          <p className="hint">Если мы ошиблись — выберите правильное значение в списке.</p>
          <div className="table-scroll" tabIndex={0} role="region" aria-label="Сопоставление столбцов">
            <table className="data-table cols-table stack-sm">
              <thead><tr><th scope="col">Столбец в файле</th><th scope="col">Что это</th><th scope="col">Уверенность</th><th scope="col">Пример значения</th></tr></thead>
              <tbody>
                {parsed.columns.map((c) => (
                  <tr key={c.index}>
                    <td><strong>{c.header}</strong></td>
                    <td data-label="Что это">
                      <label className="sr-only" htmlFor={`col-${c.index}`}>Назначение столбца «{c.header}»</label>
                      <select id={`col-${c.index}`} value={c.field} onChange={(e) => setField(c.index, e.target.value as FieldKey)}>
                        {FIELDS.map((f) => <option key={f} value={f}>{FIELD_LABELS[f]}</option>)}
                      </select>
                    </td>
                    <td data-label="Уверенность"><span className={`conf conf-${c.confidence === 'точно' ? 'ok' : c.confidence === 'вероятно' ? 'mid' : 'no'}`}>{c.confidence}</span></td>
                    <td className="sample-cell" data-label="Пример значения">{c.sample.slice(0, 90)}{c.sample.length > 90 ? '…' : ''}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <h4>Итог разбора</h4>
          <div className="parse-stats">
            <div><span className="big-num">{preview.length}</span> позиций</div>
            <div><span className="big-num">{preview.filter((p) => p.цена !== null).length}</span> с ценой</div>
            <div><span className="big-num">{preview.filter((p) => Object.keys(p.характеристики).length > 0).length}</span> с разобранными характеристиками</div>
            <div><span className="big-num">{cats.length}</span> категорий</div>
          </div>

          <div className="table-scroll" tabIndex={0} role="region" aria-label="Первые позиции">
            <table className="data-table stack-sm">
              <thead><tr><th scope="col">Артикул</th><th scope="col">Наименование</th><th scope="col">Категория</th><th scope="col">Характеристики (разобрано)</th><th scope="col" className="num">Цена</th></tr></thead>
              <tbody>
                {preview.slice(0, 8).map((p) => (
                  <tr key={p.артикул + p.наименование}>
                    <td className="mono" data-label="Артикул">{p.артикул}</td>
                    <td data-label="Наименование"><b>{p.наименование}</b></td>
                    <td data-label="Категория">{p.категория}</td>
                    <td className="specs-cell" data-label="Характеристики">{Object.entries(p.характеристики).slice(0, 4).map(([k, v]) => <span key={k} className="spec-chip">{k}: <b>{v}</b></span>)}{Object.keys(p.характеристики).length > 4 && <span className="more">ещё {Object.keys(p.характеристики).length - 4}</span>}</td>
                    <td className="num" data-label="Цена">{rub(p.цена)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {preview.length > 8 && <p className="hint">Показаны первые 8 из {preview.length}.</p>}

          <div className="cta-row">
            <button type="button" className="btn btn-solid" onClick={save} disabled={!preview.length}>Сохранить ассортимент</button>
            {saved && <span className="saved" role="status">Сохранено. <a href={href('/demo/tendery')}>Перейти к подходящим тендерам →</a></span>}
          </div>
        </section>
      )}

      {!parsed && (
        <section>
          <h3 className="h3-rule">Категории в ассортименте</h3>
          <ul className="cat-list">
            {cats.map(([c, n]) => <li key={c}><span>{c}</span><b>{n}</b></li>)}
          </ul>
          <details className="legend all-models">
            <summary>Показать все {catalog.length} {catalog.length === 1 ? 'позицию' : 'позиций'} ассортимента</summary>
            <div className="table-scroll" tabIndex={0} role="region" aria-label="Все позиции ассортимента">
              <table className="data-table stack-sm">
                <thead><tr><th scope="col">Артикул</th><th scope="col">Модель</th><th scope="col">Категория</th><th scope="col">Что известно о реестрах</th><th scope="col" className="num">Цена</th></tr></thead>
                <tbody>
                  {catalog.map((p) => (
                    <tr key={p.артикул + p.наименование}>
                      <td className="mono" data-label="Артикул">{p.артикул}</td>
                      <td data-label="Модель"><b>{p.наименование}</b>{p.источник_url && <> <a className="src-link" href={p.источник_url} target="_blank" rel="noopener noreferrer">страница производителя</a></>}</td>
                      <td data-label="Категория">{p.категория}</td>
                      <td className="specs-cell" data-label="Реестры">{p.реестр || (p.страна ? `страна: ${p.страна}` : '—')}</td>
                      <td className="num" data-label="Цена">{p.цена ? rub(p.цена) : 'нет данных'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
          <p className="hint">Дальше: <a href={href('/demo/tendery')}>подходящие тендеры →</a></p>
        </section>
      )}
    </>
  );
}
