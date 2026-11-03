// Подхват результатов других блоков перед сборкой (запускается сам перед `npm run build`).
//
// 1. Блок G (движок сверки) кладёт файлы в  ../движок/демо_выход/<номер_закупки>.json
//    Если они есть и в правильном формате — копируем в src/data/sverka_engine/,
//    и сайт показывает их ВМЕСТО наших демо-примеров из src/data/sverka/.
// 2. Блок H (модуль цены) кладёт ../цена/для_демо.json — копируем в src/data/price_table_h.json,
//    и блок «Цена» берёт медианы оттуда, а не из нашей оценки price_table_own.json.
//
// 3. Каталог движка ../движок/каталог_демо.xlsx -> src/data/catalog_demo.json (раздел «Ваш ассортимент» по умолчанию)
//    и копия xlsx в public/ для скачивания. Нужен python3 с openpyxl; нет — остаётся прошлый json.
// 4. Статьи и частые вопросы (блок L) ../контент/*.md -> src/data/articles.json (markdown сразу в HTML, при сборке).
//
// Ничего нет — ничего не ломается: остаются наши демо-файлы.
import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync, rmSync, copyFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { Marked } from 'marked';
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
    нацрежим_в_извещении: z['нацрежим_в_извещении'] === true ? true : z['нацрежим_в_извещении'] === false ? false : null, разобрано: z['разобрано'] || '',
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
        причина: typeof sv['причина'] === 'string' ? sv['причина'] : '',
        проверить: Array.isArray(sv['проверить']) ? sv['проверить'].map(String) : [],
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

// ---- 3. Каталог движка ----
const catSrc = join(cloud, 'движок', 'каталог_демо.xlsx');
const catDst = join(proto, 'src', 'data', 'catalog_demo.json');
if (existsSync(catSrc)) {
  const r = spawnSync('python3', [join(proto, 'scripts', 'make_catalog_demo.py'), catSrc, catDst], { encoding: 'utf8' });
  if (r.status === 0) {
    process.stdout.write(r.stdout);
    copyFileSync(catSrc, join(proto, 'public', 'katalog_demo.xlsx'));
  } else {
    console.warn('[sync] каталог не разобран (нужны python3 и openpyxl), остаётся прошлый catalog_demo.json:', (r.stderr || '').split('\n').slice(-3).join(' '));
  }
} else {
  console.log('[sync] движок/каталог_демо.xlsx нет — по умолчанию останется пример прайса');
}

// ---- 4. Статьи и FAQ ----
const contentDir = join(cloud, 'контент');
const articlesDst = join(proto, 'src', 'data', 'articles.json');
function frontMatter(text) {
  const m = /^---\n([\s\S]*?)\n---\n?([\s\S]*)$/.exec(text.replace(/\r\n/g, '\n'));
  if (!m) return { meta: {}, body: text };
  const meta = {};
  for (const line of m[1].split('\n')) {
    const k = /^([\w-]+):\s*(.*)$/.exec(line);
    if (!k) continue;
    let v = k[2].trim();
    if (v.startsWith('[') && v.endsWith(']')) v = v.slice(1, -1).split(',').map((x) => x.trim()).filter(Boolean);
    meta[k[1]] = v;
  }
  return { meta, body: m[2] };
}
function makeMarked(slugs) {
  const md = new Marked({ gfm: true });
  md.use({
    renderer: {
      link({ href, title, tokens }) {
        const text = this.parser.parseInline(tokens);
        let to = href, ext = false;
        if (href === '#pilot') to = '#/pilot'; // форма «Хочу пилот» на лендинге
        else if (/^\/[\w-]+$/.test(href) && slugs.has(href.slice(1))) to = '#/stati/' + href.slice(1);
        else if (/^https?:/.test(href)) ext = true;
        return `<a href="${to}"${title ? ` title="${title}"` : ''}${ext ? ' target="_blank" rel="noopener noreferrer"' : ''}>${text}</a>`;
      },
      html() { return ''; }, // сырой HTML из статей не пропускаем
    },
  });
  return md;
}
if (existsSync(contentDir)) {
  const files = readdirSync(contentDir).filter((f) => f.endsWith('.md') && f !== 'README.md').sort();
  const parsed = files.map((f) => ({ f, ...frontMatter(readFileSync(join(contentDir, f), 'utf8')) }));
  const slugs = new Set(parsed.map((p) => String(p.meta.slug || '')));
  const md = makeMarked(slugs);
  const articles = [], faq = [];
  for (const p of parsed) {
    const slug = String(p.meta.slug || p.f.replace(/\.md$/, ''));
    if (p.f.startsWith('faq')) {
      // «## Тема» -> «### N. Вопрос» -> ответ
      const groups = [];
      let cur = null, q = null;
      for (const tok of md.lexer(p.body)) {
        if (tok.type === 'heading' && tok.depth === 2) { cur = { тема: tok.text, вопросы: [] }; groups.push(cur); q = null; }
        else if (tok.type === 'heading' && tok.depth === 3 && cur) { q = { вопрос: tok.text.replace(/^\d+\.\s*/, ''), токены: [] }; cur.вопросы.push(q); }
        else if (q && tok.type !== 'hr' && tok.type !== 'space') q.токены.push(tok);
      }
      for (const g of groups) faq.push({ тема: g.тема, вопросы: g.вопросы.map((x) => ({ вопрос: x.вопрос, ответ: md.parser(Object.assign(x.токены, { links: {} })) })) });
      continue;
    }
    // убираем заголовок h1 (он выводится отдельно) и вводную строку «не юридическая консультация» оставляем как есть
    const all = md.lexer(p.body);
    const h1 = (all.find((t) => t.type === 'heading' && t.depth === 1) || {}).text || '';
    const tokens = all.filter((t, i, a) => !(t.type === 'heading' && t.depth === 1));
    const html = md.parser(Object.assign(tokens, { links: {} }));
    const words = p.body.split(/\s+/).filter(Boolean).length;
    articles.push({ slug, title: String(p.meta.title || slug), заголовок: h1 || String(p.meta.title || slug), description: String(p.meta.description || ''), date: String(p.meta.date || ''), tags: Array.isArray(p.meta.tags) ? p.meta.tags : [], слов: words, html, файл: p.f });
  }
  const faqCount = faq.reduce((s, g) => s + g.вопросы.length, 0);
  writeFileSync(articlesDst, JSON.stringify({ статьи: articles, faq }));
  console.log(`[sync] статьи (блок L): ${articles.length}, частых вопросов: ${faqCount}`);
} else {
  writeFileSync(articlesDst, JSON.stringify({ статьи: [], faq: [] }));
  console.log('[sync] контент/ нет — раздел статей будет пустым');
}
