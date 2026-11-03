import { snapshot } from '../lib/data';

function snapDate(): string {
  const d = new Date(snapshot.снято);
  if (Number.isNaN(d.getTime())) return snapshot.снято;
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' });
}

export function Start({ onStart }: { onStart: () => void }) {
  return (
    <section className="start" aria-labelledby="mega">
      <div className="dots" aria-hidden="true"><i /></div>
      <div className="start-body">
        <h1 className="mega" id="mega"><span>Тендеры</span><span>под</span><span>ключ</span></h1>
        <p className="start-line">Найдём подходящие тендеры, сверим с вашим ассортиментом и подскажем цену. 6 шагов, около 5 минут</p>
        <div className="start-foot">
          <button className="btn primary" onClick={onStart}>Начать</button>
          <p className="mono dim">Тендеры: снимок ЕИС на {snapDate()}{snapshot.пример ? ' · пример' : ''}</p>
        </div>
      </div>
    </section>
  );
}
