// Проверка работы собранного сайта (dist/index.html, открыт как файл, без сервера):
// загрузка XLSX-прайса с заголовком над шапкой, сохранение ассортимента, фильтры тендеров,
// пересчёт сверки, разбор вставленного техзадания, скачивание .docx и .csv, форма пилота.
// Запуск: npm run build && node scripts/smoke_test.mjs
import { createRequire } from 'node:module';
import { join, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { statSync } from 'node:fs';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const base = pathToFileURL(join(root, 'dist', 'index.html')).href;
const results = [];
const ok = (name, cond, extra = '') => { results.push(`${cond ? 'OK  ' : 'FAIL'} ${name}${extra ? ' — ' + extra : ''}`); };

const browser = await chromium.launch(process.env.PW_CHROMIUM ? { executablePath: process.env.PW_CHROMIUM } : {});
const ctx = await browser.newContext({ acceptDownloads: true, viewport: { width: 1280, height: 900 } });
const page = await ctx.newPage();
const errors = [];
page.on('pageerror', (e) => errors.push(e.message));

// 1. Ассортимент: XLSX с пометкой в первой строке, шапка в третьей
await page.goto(base + '#/demo/assortiment');
await page.setInputFiles('input[type=file]', join(root, 'public', 'пример_прайса_оргтехники.xlsx'));
await page.waitForSelector('.parse-result', { timeout: 10000 });
const notes = await page.locator('.parse-result .notes').innerText();
ok('XLSX: шапка найдена в строке 3', notes.includes('строке 3'), notes.split('\n').join(' | '));
const posCount = await page.locator('.parse-stats .big-num').first().innerText();
ok('XLSX: 47 позиций', posCount.trim() === '47', posCount);
await page.getByRole('button', { name: 'Сохранить ассортимент' }).click();
ok('Ассортимент сохранён', await page.locator('.saved').isVisible());

// 2. Тендеры: фильтры
await page.goto(base + '#/demo/tendery');
const total = await page.locator('.list-head b').innerText();
await page.locator('select').nth(1).selectOption('44-ФЗ');
const only44 = await page.locator('.list-head b').innerText();
ok('Фильтр по закону сужает список', Number(only44) < Number(total) && Number(only44) > 0, `${total} → ${only44}`);
await page.locator('input[type=search]').fill('телефон');
const tel = await page.locator('.list-head b').innerText();
ok('Поиск по словам работает', Number(tel) > 0 && Number(tel) < Number(only44), `«телефон» в 44-ФЗ: ${tel}`);

// 3. Карточка со сверкой: пересчёт по ассортименту и разбор вставленного техзадания
await page.goto(base + '#/demo/tender/' + encodeURIComponent('s-ДЕМО-0001'));
const before = await page.locator('.tally').innerText();
await page.getByRole('button', { name: /Пересчитать/ }).click();
const after = await page.locator('.tally').innerText();
ok('Пересчёт сверки по ассортименту', after.length > 0, `было: ${before.replace(/\s+/g, ' ')} / стало: ${after.replace(/\s+/g, ' ')}`);
await page.locator('.tz-box summary').click();
await page.getByRole('button', { name: 'Вставить пример техзадания' }).click();
await page.getByRole('button', { name: 'Разобрать и сверить' }).click();
await page.waitForSelector('text=Показан разбор вставленного текста', { timeout: 5000 });
const rows = await page.locator('.sverka-list > li').count();
const tally = (await page.locator('.tally').innerText()).replace(/\s+/g, ' ');
ok('Разбор вставленного техзадания (демо-правила)', rows === 4, `позиций: ${rows}; итог: ${tally}`);

// 4. Черновик: скачивание .docx и .csv
await page.goto(base + '#/demo/zayavka/' + encodeURIComponent('s-ДЕМО-0001'));
const [d1] = await Promise.all([page.waitForEvent('download'), page.getByRole('button', { name: /Скачать черновик/ }).click()]);
const p1 = await d1.path();
ok('Скачивается .docx', d1.suggestedFilename().endsWith('.docx') && statSync(p1).size > 5000, `${d1.suggestedFilename()}, ${statSync(p1).size} байт`);
const [d2] = await Promise.all([page.waitForEvent('download'), page.getByRole('button', { name: /Таблица характеристик/ }).click()]);
const p2 = await d2.path();
ok('Скачивается .csv', d2.suggestedFilename().endsWith('.csv') && statSync(p2).size > 500, `${d2.suggestedFilename()}, ${statSync(p2).size} байт`);

// 5. Сроки: смена срока поставки меняет дату оплаты
await page.goto(base + '#/demo/sroki/' + encodeURIComponent('s-ДЕМО-0001'));
const pay1 = await page.locator('.tl-step').last().locator('.tl-date b').innerText();
await page.getByLabel('Срок поставки, календ. дней').fill('60');
const pay2 = await page.locator('.tl-step').last().locator('.tl-date b').innerText();
ok('Срок поставки сдвигает оплату', pay1 !== pay2, `${pay1} → ${pay2}`);

// 6. Форма пилота: только localStorage
await page.goto(base + '#/');
await page.locator('input[name=name]').fill('Тест');
await page.locator('input[name=contact]').fill('t@example.com');
await page.getByRole('button', { name: 'Отправить заявку' }).click();
const saved = await page.evaluate(() => JSON.parse(localStorage.getItem('tpk_pilot_requests') || '[]').length);
ok('Форма пилота пишет в localStorage и показывает «спасибо»', saved >= 1 && await page.locator('.thanks').isVisible());

ok('Нет ошибок JavaScript', errors.length === 0, errors.join('; '));
await browser.close();
console.log(results.join('\n'));
process.exit(results.some((r) => r.startsWith('FAIL')) ? 1 : 0);
