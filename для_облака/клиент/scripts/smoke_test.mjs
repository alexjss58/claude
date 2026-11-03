// Проход всего пути на собранном dist/index.html: телефон 402×874 и компьютер 1440×900.
// Старт → 1 → 2 → 3 → 4 (пример) → 5 (правила) → 6 → «Хочу подать». Скриншоты — в скриншоты/.
// Запуск: npm run build && node scripts/smoke_test.mjs
import { createRequire } from 'node:module';
import { join, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { mkdirSync, readFileSync } from 'node:fs';

const require = createRequire(import.meta.url);
let playwright;
try { playwright = require('playwright'); } catch { playwright = require('/opt/node22/lib/node_modules/playwright'); }
const { chromium } = playwright;

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const url = pathToFileURL(join(root, 'dist', 'index.html')).href;
const shots = join(root, 'скриншоты');
mkdirSync(shots, { recursive: true });

const results = [];
const ok = (name, cond, extra = '') => { results.push({ ok: !!cond, line: `${cond ? 'OK  ' : 'FAIL'} ${name}${extra ? ' — ' + extra : ''}` }); };

const browser = await chromium.launch(process.env.PW_CHROMIUM ? { executablePath: process.env.PW_CHROMIUM } : (process.env.PLAYWRIGHT_BROWSERS_PATH ? {} : { executablePath: '/opt/pw-browsers/chromium-1243/chrome-linux64/chrome' }));

// Подделка window.claude (как на claude.ai): sample.json отвечает по первому кандидату, downloads запоминает файл
const MOCK = () => {
  window.__saved = [];
  window.__prompts = [];
  const sample = {
    json: async (prompt) => {
      window.__prompts.push(prompt);
      const m = /ПОЗИЦИИ ТЕНДЕРА \(JSON\):\n(.*)\nПРАЙС/.exec(prompt);
      const pos = JSON.parse(m[1]);
      const items = JSON.parse(prompt.split('КАНДИДАТЫ (JSON):\n')[1]);
      return pos.map((p) => { const it = items.find((i) => i.id === p['кандидаты'][0]); return { '№': p['№'], 'статус': it ? 'подходит' : 'нет', 'товар': it ? it['наименование'] : '', 'расхождения': [], 'комментарий': 'проверено моком' }; });
    },
  };
  window.claude = { use: async (n) => (n === 'sample' ? sample : n === 'downloads' ? { save: async (r) => { window.__saved.push(r.filename); return { status: 'saved' }; } } : null) };
};

async function run(tag, ctxOpts, dark = false, mockAi = false) {
  const ctx = await browser.newContext({ ...ctxOpts, acceptDownloads: true, colorScheme: dark ? 'dark' : 'light' });
  const page = await ctx.newPage();
  if (mockAi) await page.addInitScript(MOCK);
  const errors = [], external = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
  page.on('request', (r) => { const u = r.url(); if (!u.startsWith('file:') && !u.startsWith('data:') && !u.startsWith('blob:')) external.push(u); });
  const shot = async (name) => { await page.waitForTimeout(250); await page.screenshot({ path: join(shots, `${tag}_${name}.png`), fullPage: true }); };
  const noHScroll = async (name) => {
    const r = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth, bw: document.body.scrollWidth }));
    ok(`${tag}: ${name}: нет горизонтальной прокрутки`, r.sw <= r.cw + 0 && r.bw <= r.cw, JSON.stringify(r));
  };
  const click = async (name) => { await page.getByRole('button', { name, exact: false }).first().click(); };

  await page.goto(url);
  await page.waitForSelector('.mega');
  ok(`${tag}: старт открылся`, await page.locator('.mega').isVisible());
  await noHScroll('старт'); await shot('0_старт');
  await page.getByRole('button', { name: 'Начать', exact: true }).click();

  // 1
  await page.waitForSelector('text=Есть электронная подпись?');
  await page.getByRole('button', { name: 'Дальше' }).click({ force: true }); // кнопка с aria-disabled: Playwright не жмёт без force
  ok(`${tag}: шаг 1 не пускает без названия`, await page.locator('.err').first().isVisible());
  await shot('1a_компания_ошибка');
  await page.getByLabel('Название').fill('ООО «Тест-Поставка»');
  await page.getByLabel('ИНН (необязательно)').fill('123');
  await page.getByLabel('ИНН (необязательно)').blur();
  await page.getByRole('button', { name: 'Дальше' }).click({ force: true }); // кнопка с aria-disabled: Playwright не жмёт без force
  ok(`${tag}: неверный ИНН блокирует`, await page.locator('text=10 цифр').first().isVisible());
  await page.getByLabel('ИНН (необязательно)').fill('7707083893');
  await page.getByRole('combobox').fill('Моск');
  await page.getByRole('option', { name: /^Москва/ }).first().click();
  await page.getByRole('radio', { name: 'Да', exact: true }).click();
  await noHScroll('шаг 1'); await shot('1_компания');
  await click('Дальше');

  // 2
  await page.waitForSelector('.tiles');
  await page.getByRole('button', { name: /Компьютеры и оргтехника/ }).click();
  await page.getByRole('button', { name: /Связь и сети/ }).click();
  await page.getByRole('radio', { name: 'Вся Россия' }).click();
  await noHScroll('шаг 2'); await shot('2_запрос');
  await page.getByRole('button', { name: 'Найти тендеры' }).click();

  // 3
  await page.waitForSelector('.searching');
  await shot('3a_поиск');
  await page.waitForSelector('.tcard', { timeout: 8000 });
  const nCards = await page.locator('.tcard').count();
  ok(`${tag}: шаг 3 есть результаты`, nCards > 0, `${nCards} карточек`);
  ok(`${tag}: отмечено не больше 5`, (await page.locator('.tcard .pick[aria-pressed="true"]').count()) <= 5 && (await page.locator('.tcard .pick[aria-pressed="true"]').count()) > 0);
  await noHScroll('шаг 3'); await shot('3_тендеры');
  await click('К ассортименту');

  // 4
  await page.waitForSelector('text=Нет файла');
  await shot('4a_ассортимент');
  await page.getByRole('button', { name: 'Нет файла — показать на примере' }).click();
  await page.waitForSelector('.got');
  const got = await page.locator('.got').innerText();
  ok(`${tag}: демо-каталог разобран`, /58/.test(got), got.replace(/\s+/g, ' '));
  ok(`${tag}: в мини-таблице 5 строк`, (await page.locator('.mini tbody tr').count()) === 5);
  await noHScroll('шаг 4'); await shot('4_ассортимент');
  await click('К анализу');

  // 5
  if (mockAi) {
    await page.getByRole('button', { name: 'Начать анализ' }).click();
    await page.waitForSelector('.modetag:has-text("ИИ (Claude)")');
    ok(`${tag}: метка «Сверка: ИИ (Claude)»`, true);
    ok(`${tag}: ИИ вызван по разу на тендер`, (await page.evaluate(() => window.__prompts.length)) === 5, String(await page.evaluate(() => window.__prompts.length)));
  }
  await page.waitForSelector('.tres');
  const nRes = await page.locator('.tres').count();
  ok(`${tag}: шаг 5 есть анализ`, nRes > 0, `${nRes} тендеров`);
  if (!mockAi) ok(`${tag}: метка режима`, await page.locator('text=Сверка: правила').first().isVisible());
  ok(`${tag}: есть «Закрываете X из Y»`, (await page.locator('.close-line').first().innerText()).includes('из'));
  const st = await page.evaluate(() => ({ ok: document.querySelectorAll('.pos .badge.ok').length, almost: document.querySelectorAll('.pos .badge.almost').length, no: document.querySelectorAll('.pos .badge.no').length }));
  console.log(`  [${tag}] статусы позиций: подходит ${st.ok}, почти ${st.almost}, нет ${st.no}`);
  await noHScroll('шаг 5'); await shot('5_анализ');
  await click('К цене');

  // 6
  await page.waitForSelector('.pcard');
  ok(`${tag}: шаг 6 есть цена`, (await page.locator('.offer').count()) > 0);
  await page.locator('.pcard').first().getByRole('radio', { name: '5+' }).click();
  await page.locator('.pcard').first().getByLabel('Ваша себестоимость, ₽').fill('100000');
  await noHScroll('шаг 6'); await shot('6_цена');
  // CSV
  if (mockAi) {
    await page.getByRole('button', { name: 'Скачать итог (CSV)' }).click();
    await page.waitForTimeout(300);
    ok(`${tag}: CSV ушёл через downloads`, (await page.evaluate(() => window.__saved)).some((n) => n.endsWith('.csv')));
  } else {
    const [dl] = await Promise.all([page.waitForEvent('download', { timeout: 5000 }), page.getByRole('button', { name: 'Скачать итог (CSV)' }).click()]);
    ok(`${tag}: CSV скачивается`, /\.csv$/.test(dl.suggestedFilename()), dl.suggestedFilename());
  }
  // Хочу подать: кнопка внизу экрана прокручивает к форме
  await page.locator('.nav').getByRole('button', { name: 'Хочу подать с вами' }).click();
  await page.waitForTimeout(500);
  ok(`${tag}: форма контакта на экране`, await page.locator('#contact').isVisible());
  await page.locator('.final').getByRole('button', { name: 'Отправить контакт' }).click();
  ok(`${tag}: без согласия не отправляется`, await page.locator('.err[role="alert"]').last().isVisible());
  await page.getByLabel(/Телефон или Telegram/i).fill('+7 900 123-45-67');
  await page.getByRole('checkbox', { name: 'Согласие на обработку данных' }).click();
  await page.locator('.final').getByRole('button', { name: 'Отправить контакт' }).click();
  await page.waitForSelector('text=Спасибо, свяжемся');
  ok(`${tag}: «Спасибо, свяжемся»`, true);
  await noHScroll('итог'); await shot('7_итог');

  // состояние переживает перезагрузку
  await page.reload();
  await page.waitForSelector('.pcard');
  ok(`${tag}: после перезагрузки остались на шаге 6`, await page.locator('text=Спасибо, свяжемся').isVisible());
  // «Начать заново»
  await page.getByRole('button', { name: 'Начать заново' }).click();
  await page.getByRole('button', { name: 'Да', exact: true }).click();
  await page.waitForSelector('.mega');
  ok(`${tag}: «Начать заново» вернул на старт`, true);

  ok(`${tag}: нет ошибок JS`, errors.length === 0, errors.slice(0, 3).join(' | '));
  ok(`${tag}: нет внешних запросов`, external.length === 0, external.slice(0, 3).join(' | '));
  await ctx.close();
}

const phone = { viewport: { width: 402, height: 874 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true,
  userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1' };
const desk = { viewport: { width: 1440, height: 900 } };
try {
  await run('телефон', phone);
  await run('компьютер', desk);
  await run('телефон_ИИ', phone, false, true);
  if (process.env.DARK) await run('тёмная', phone, true);
} catch (e) {
  ok('прогон дошёл до конца', false, e.message.split('\n').slice(0,6).join(' | '));
}
await browser.close();
for (const r of results) console.log(r.line);
const bad = results.filter((r) => !r.ok).length;
console.log(bad ? `\nПровалено: ${bad}` : '\nВсе проверки пройдены');
process.exit(bad ? 1 : 0);
