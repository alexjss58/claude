// Скриншоты всех экранов собранного сайта (dist/index.html) на компьютере и телефоне.
// Запуск: npm run build && npm run screens   → папка скриншоты/
// Открываем файл напрямую (file://) — заодно проверяем, что сайт работает без сервера.
import { createRequire } from 'node:module';
import { mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const require = createRequire(import.meta.url);
let chromium;
try {
  ({ chromium } = require('playwright'));
} catch {
  ({ chromium } = require('@playwright/test'));
}

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const out = join(root, 'скриншоты');
mkdirSync(out, { recursive: true });
const base = pathToFileURL(join(root, 'dist', 'index.html')).href;

const firstSverka = 's-ДЕМО-0001';
const screens = [
  { name: '01_лендинг', hash: '#/' },
  { name: '02_ассортимент', hash: '#/demo/assortiment', action: async (p) => { await p.getByRole('button', { name: 'Взять пример прайса' }).click(); await p.waitForTimeout(300); } },
  { name: '03_подходящие_тендеры', hash: '#/demo/tendery' },
  { name: '04_карточка_тендера_со_сверкой', hash: `#/demo/tender/${encodeURIComponent(firstSverka)}` },
  { name: '05_карточка_тендера_из_выгрузки', hash: '#/demo/tendery', action: async (p) => { await p.locator('.tender-row .tr-title').first().click(); await p.waitForTimeout(300); } },
  { name: '06_черновик_заявки', hash: `#/demo/zayavka/${encodeURIComponent(firstSverka)}` },
  { name: '07_сроки_и_деньги', hash: `#/demo/sroki/${encodeURIComponent(firstSverka)}` },
  { name: '08_форма_пилота_спасибо', hash: '#/', action: async (p) => {
    await p.locator('input[name=name]').fill('Иван (тест)');
    await p.locator('input[name=contact]').fill('test@example.com');
    await p.getByRole('button', { name: 'Отправить заявку' }).click();
    await p.waitForTimeout(200);
    await p.locator('.thanks').scrollIntoViewIfNeeded();
  }, viewportOnly: true },
];

const devices = [
  { tag: 'компьютер', viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 },
  { tag: 'телефон', viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true },
];

const only = process.argv[2];
const browser = await chromium.launch(process.env.PW_CHROMIUM ? { executablePath: process.env.PW_CHROMIUM } : {});
const errors = [];
for (const d of devices) {
  const ctx = await browser.newContext({ viewport: d.viewport, deviceScaleFactor: d.deviceScaleFactor, isMobile: d.isMobile, hasTouch: d.hasTouch, locale: 'ru-RU' });
  for (const s of screens) {
    if (only && !s.name.includes(only)) continue;
    const page = await ctx.newPage();
    page.on('pageerror', (e) => errors.push(`${d.tag} ${s.name}: ${e.message}`));
    page.on('console', (m) => { if (m.type() === 'error') errors.push(`${d.tag} ${s.name}: console ${m.text()}`); });
    await page.goto(base + s.hash);
    await page.waitForTimeout(500);
    if (s.action) await s.action(page);
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(200);
    const file = join(out, `${s.name}__${d.tag}.png`);
    await page.screenshot({ path: file, fullPage: !s.viewportOnly });
    // Проверка на горизонтальную прокрутку страницы (на телефоне её быть не должно)
    const overflow = await page.evaluate(() => {
      const w = window.innerWidth;
      const bad = [...document.querySelectorAll('body *')].filter((e) => {
        if (e.closest('.table-scroll')) return false; // таблицы листаются внутри своей рамки — это нормально
        const r = e.getBoundingClientRect();
        return r.width > 0 && r.right > w + 1;
      }).slice(0, 5).map((e) => `${e.tagName.toLowerCase()}.${String(e.className).split(' ')[0]} (${Math.round(e.getBoundingClientRect().right)}px)`);
      return { page: document.documentElement.scrollWidth - w, bad };
    });
    if (overflow.page > 1) errors.push(`${d.tag} ${s.name}: горизонтальная прокрутка ${overflow.page}px`);
    if (overflow.bad.length) errors.push(`${d.tag} ${s.name}: за правый край вылезают ${overflow.bad.join(', ')}`);
    console.log('✓', file.replace(root + '/', ''));
    await page.close();
  }
  await ctx.close();
}
await browser.close();
if (errors.length) { console.log('\nЗамечания:\n' + errors.join('\n')); } else { console.log('\nОшибок в консоли нет.'); }
