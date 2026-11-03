// Подхват результатов других блоков перед сборкой (запускается сам перед `npm run build`).
//
// 1. Блок G (движок сверки) кладёт файлы в  ../движок/демо_выход/<номер_закупки>.json
//    Если они есть и в правильном формате — копируем в src/data/sverka_engine/,
//    и сайт показывает их ВМЕСТО наших демо-примеров из src/data/sverka/.
// 2. Блок H (модуль цены) кладёт ../цена/для_демо.json — копируем в src/data/price_table_h.json,
//    и блок «Цена» берёт медианы оттуда, а не из нашей оценки price_table_own.json.
//
// Ничего нет — ничего не ломается: остаются наши демо-файлы.
import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const proto = join(dirname(fileURLToPath(import.meta.url)), '..');
const cloud = join(proto, '..');

// Приводим файл движка к виду, который ожидает сайт: недостающие поля — пустыми значениями,
// итог пересчитываем по позициям (на случай, если движок его не заполнил).
function normalize(d, file) {
  const z = d['закупка'] || {};
  const zakupka = {
    номер: String(z['номер'] ?? file.replace(/\.json$/, '')), предмет: z['предмет'] || 'Закупка', заказчик: z['заказчик'] || '',
    инн_заказчика: String(z['инн_заказчика'] ?? ''), закон: z['закон'] || '44-ФЗ', способ: z['способ'] || '', нмц: Number(z['нмц']) || 0,
    регион: z['регион'] || '', дата_окончания: z['дата_окончания'] || '', ссылка: z['ссылка'] || '', источник_документа: z['источник_документа'] || '',
  };
  const statuses = ['подходит', 'почти', 'нет'];
  const pos = d['позиции'].map((p, i) => {
    const sv = p['сверка'] || {};
    return {
      '№': Number(p['№'] ?? i + 1), наименование: p['наименование'] || `Позиция ${i + 1}`, ктру: p['ктру'] || '', окпд2: p['окпд2'] || '',
      количество: Number(p['количество']) || 0, единица: p['единица'] || 'шт',
      характеристики: Array.isArray(p['характеристики']) ? p['характеристики'].map((c) => ({
        имя: c['имя'] || '', условие: c['условие'] || 'текст', значение: String(c['значение'] ?? ''), единица: c['единица'] || '',
        эквивалент_допускается: c['эквивалент_допускается'] !== false,
      })) : [],
      сверка: {
        статус: statuses.includes(sv['статус']) ? sv['статус'] : 'нет', товар_из_каталога: sv['товар_из_каталога'] || '', артикул: String(sv['артикул'] ?? ''),
        расхождения: Array.isArray(sv['расхождения']) ? sv['расхождения'] : [],
      },
    };
  });
  const итог = { подходит: 0, почти: 0, нет: 0 };
  for (const p of pos) итог[p.сверка.статус]++;
  return { закупка: zakupka, позиции: pos, итог, режим: d['режим'] || 'демо' };
}

const engineSrc = process.env.ENGINE_DIR || join(cloud, 'движок', 'демо_выход'); // ENGINE_DIR — для проверки на своих файлах
const engineDst = join(proto, 'src', 'data', 'sverka_engine');
rmSync(engineDst, { recursive: true, force: true });
mkdirSync(engineDst, { recursive: true });
let ok = 0, bad = 0;
if (existsSync(engineSrc)) {
  for (const f of readdirSync(engineSrc).filter((x) => x.endsWith('.json'))) {
    try {
      const d = JSON.parse(readFileSync(join(engineSrc, f), 'utf8'));
      if (!d || typeof d !== 'object' || !d['закупка'] || !Array.isArray(d['позиции'])) throw new Error('не тот формат');
      writeFileSync(join(engineDst, f.replace(/[^\w.-]+/g, '_')), JSON.stringify(normalize(d, f)));
      ok++;
    } catch (e) {
      bad++;
      console.warn(`[sync] пропускаю ${f}: ${e.message}`);
    }
  }
}
writeFileSync(join(engineDst, '.keep'), '');
console.log(`[sync] сверки из движка (блок G): ${ok} файлов${bad ? `, пропущено ${bad}` : ''}${ok ? '' : ' — останутся демо-примеры'}`);

const priceSrc = join(cloud, 'цена', 'для_демо.json');
const priceDst = join(proto, 'src', 'data', 'price_table_h.json');
rmSync(priceDst, { force: true });
if (existsSync(priceSrc)) {
  try {
    const d = JSON.parse(readFileSync(priceSrc, 'utf8'));
    if (!Array.isArray(d)) throw new Error('ожидался массив');
    writeFileSync(priceDst, JSON.stringify(d));
    console.log(`[sync] таблица цены из блока H: ${d.length} строк`);
  } catch (e) {
    console.warn(`[sync] цена/для_демо.json не подошёл: ${e.message} — беру свою оценку`);
  }
} else {
  console.log('[sync] цена/для_демо.json нет — беру свою оценку из выгрузок');
}
