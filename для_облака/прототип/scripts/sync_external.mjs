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

const engineSrc = join(cloud, 'движок', 'демо_выход');
const engineDst = join(proto, 'src', 'data', 'sverka_engine');
rmSync(engineDst, { recursive: true, force: true });
mkdirSync(engineDst, { recursive: true });
let ok = 0, bad = 0;
if (existsSync(engineSrc)) {
  for (const f of readdirSync(engineSrc).filter((x) => x.endsWith('.json'))) {
    try {
      const d = JSON.parse(readFileSync(join(engineSrc, f), 'utf8'));
      if (!d || typeof d !== 'object' || !d['закупка'] || !Array.isArray(d['позиции'])) throw new Error('не тот формат');
      writeFileSync(join(engineDst, f.replace(/[^\w.-]+/g, '_')), JSON.stringify(d));
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
