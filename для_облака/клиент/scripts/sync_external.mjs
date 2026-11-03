// Подхват данных перед сборкой (запускается сам перед `npm run build`).
//  1. data/снимок.json (готовит другой агент) — если нет, берём data/_пример_снимка.json.
//  2. data/регионы.json — если нет, data/_пример_регионов.json.
//  3. ../цена/для_демо.json — таблица цены (ниша × закон × способ × участников).
//  4. ../движок/каталог_демо.csv — демо-каталог «Нет файла — показать на примере».
// Результат складывается в src/data/ (генерируется, руками не править).
import { existsSync, mkdirSync, readFileSync, writeFileSync, copyFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const cloud = join(root, '..');
const out = join(root, 'src', 'data');
mkdirSync(out, { recursive: true });

function pick(real, example, dst, check, what) {
  const tryRead = (p) => {
    if (!existsSync(p)) return null;
    try { const d = JSON.parse(readFileSync(p, 'utf8')); check(d); return d; }
    catch (e) { console.warn(`[sync] ${p} не подошёл: ${e.message}`); return null; }
  };
  let d = tryRead(real), used = real, example_ = false;
  if (!d) { d = tryRead(example); used = example; example_ = true; }
  if (!d) throw new Error(`Нет ни ${real}, ни ${example}`);
  writeFileSync(join(out, dst), JSON.stringify(d));
  console.log(`[sync] ${what}: ${used.replace(root + '/', '')}${example_ ? ' (ПРИМЕР)' : ''}`);
  return d;
}

const snap = pick(join(root, 'data', 'снимок.json'), join(root, 'data', '_пример_снимка.json'), 'snapshot.json',
  (d) => { if (!Array.isArray(d.тендеры) || !d.снято) throw new Error('нет тендеры/снято'); }, 'снимок тендеров');
console.log(`[sync] тендеров в снимке: ${snap.тендеры.length}, снято ${snap.снято}`);
pick(join(root, 'data', 'регионы.json'), join(root, 'data', '_пример_регионов.json'), 'regions.json',
  (d) => { if (!Array.isArray(d) || !d[0]?.код) throw new Error('ожидался массив регионов'); }, 'регионы');

const price = join(cloud, 'цена', 'для_демо.json');
if (existsSync(price)) {
  const d = JSON.parse(readFileSync(price, 'utf8'));
  if (!Array.isArray(d)) throw new Error('цена/для_демо.json: ожидался массив');
  writeFileSync(join(out, 'price.json'), JSON.stringify(d));
  console.log(`[sync] таблица цены: ${d.length} строк`);
} else if (!existsSync(join(out, 'price.json'))) {
  writeFileSync(join(out, 'price.json'), '[]');
  console.warn('[sync] цена/для_демо.json нет — цена будет без рекомендации');
}

const cat = join(cloud, 'движок', 'каталог_демо.csv');
if (existsSync(cat)) { copyFileSync(cat, join(out, 'catalog_demo.csv')); console.log('[sync] демо-каталог: движок/каталог_демо.csv'); }
else if (!existsSync(join(out, 'catalog_demo.csv'))) { writeFileSync(join(out, 'catalog_demo.csv'), 'Наименование,Цена\n'); console.warn('[sync] демо-каталога нет'); }
