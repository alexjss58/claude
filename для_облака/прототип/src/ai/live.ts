// «Живой» режим слоя ИИ: разбор техзадания и сверка через Claude API.
//
// ВНИМАНИЕ. Ключ берётся из переменной окружения VITE_ANTHROPIC_API_KEY при сборке или запуске
// `npm run dev`. Vite вшивает такие переменные в код страницы, поэтому ключ виден любому,
// кто откроет сайт. Это годится ТОЛЬКО для локального теста на своём компьютере.
// Для настоящего сайта вызов нужно перенести на сервер (функция Vercel, свой бэкенд),
// а в браузер отдавать только результат. Ключи в код не кладём.

import Anthropic from '@anthropic-ai/sdk';
import type { CatalogItem, Sverka } from '../types';
import { tally } from './rules';

const MODEL = 'claude-opus-5-5';

const CHAR_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['имя', 'условие', 'значение', 'единица', 'эквивалент_допускается'],
  properties: {
    имя: { type: 'string' },
    условие: { type: 'string', enum: ['>=', '<=', '=', 'диапазон', 'из_списка', 'текст'] },
    значение: { type: 'string' },
    единица: { type: 'string' },
    эквивалент_допускается: { type: 'boolean' },
  },
};

const SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['позиции'],
  properties: {
    позиции: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['№', 'наименование', 'ктру', 'окпд2', 'количество', 'единица', 'характеристики', 'сверка'],
        properties: {
          '№': { type: 'integer' },
          наименование: { type: 'string' },
          ктру: { type: 'string' },
          окпд2: { type: 'string' },
          количество: { type: 'number' },
          единица: { type: 'string' },
          характеристики: { type: 'array', items: CHAR_SCHEMA },
          сверка: {
            type: 'object',
            additionalProperties: false,
            required: ['статус', 'товар_из_каталога', 'артикул', 'расхождения'],
            properties: {
              статус: { type: 'string', enum: ['подходит', 'почти', 'нет'] },
              товар_из_каталога: { type: 'string' },
              артикул: { type: 'string' },
              расхождения: {
                type: 'array',
                items: {
                  type: 'object',
                  additionalProperties: false,
                  required: ['характеристика', 'требуется', 'у_товара'],
                  properties: { характеристика: { type: 'string' }, требуется: { type: 'string' }, у_товара: { type: 'string' } },
                },
              },
            },
          },
        },
      },
    },
  },
};

const SYSTEM = `Ты помогаешь поставщику оргтехники и связи участвовать в тендерах (44-ФЗ, 223-ФЗ).
Тебе дают текст техзадания (описания объекта закупки) и каталог поставщика.
1) Выпиши все позиции техзадания: наименование, ОКПД2 и КТРУ (если указаны, иначе пустая строка), количество, единицу.
2) Для каждой позиции выпиши характеристики с условием: ">=" для «не менее», "<=" для «не более», "=" для точного значения, "диапазон", "из_списка", "текст". Значение — без единицы, единицу — отдельно. Отметь, допускается ли эквивалент.
3) Сверь позицию с каталогом: "подходит" — товар закрывает все проверяемые требования; "почти" — 1–2 расхождения (перечисли их: что требуется и что у товара); "нет" — подходящего товара нет.
Не придумывай характеристики, которых нет в каталоге: если значение неизвестно, не считай это расхождением, а отметь в расхождениях как «нет данных в каталоге». Отвечай по-русски.`;

export function liveKey(): string | undefined {
  const k = import.meta.env.VITE_ANTHROPIC_API_KEY as string | undefined;
  return k && k.trim() ? k.trim() : undefined;
}

export async function analyzeLive(tzText: string, catalog: CatalogItem[], base?: Partial<Sverka['закупка']>): Promise<Sverka> {
  const apiKey = liveKey();
  if (!apiKey) throw new Error('Ключ не задан: «живой» режим выключен.');
  const client = new Anthropic({ apiKey, dangerouslyAllowBrowser: true });
  const catalogText = catalog
    .slice(0, 300)
    .map((c) => `${c.артикул} | ${c.наименование} | ${c.категория} | ${c.характеристики_текст}`)
    .join('\n');
  const response = await client.beta.messages.create({
    model: MODEL,
    max_tokens: 16000,
    betas: ['server-side-fallback-2026-07-01'],
    fallbacks: 'default',
    output_config: { effort: 'medium', format: { type: 'json_schema', schema: SCHEMA } },
    system: SYSTEM,
    messages: [{
      role: 'user',
      content: `КАТАЛОГ ПОСТАВЩИКА (артикул | наименование | категория | характеристики):\n${catalogText}\n\nТЕХЗАДАНИЕ:\n${tzText}`,
    }],
  });
  if (response.stop_reason === 'refusal') throw new Error('Модель отказалась отвечать на этот запрос.');
  if (response.stop_reason === 'max_tokens') throw new Error('Ответ не поместился: техзадание слишком длинное для одного запроса.');
  const text = response.content.map((b) => (b.type === 'text' ? b.text : '')).join('');
  const parsed = JSON.parse(text) as { позиции: Sverka['позиции'] };
  return {
    закупка: {
      номер: base?.номер || '', предмет: base?.предмет || 'Техзадание из вставленного текста', заказчик: base?.заказчик || '',
      инн_заказчика: base?.инн_заказчика || '', закон: base?.закон || '', способ: base?.способ || '', нмц: base?.нмц || 0,
      регион: base?.регион || '', дата_окончания: base?.дата_окончания || '', ссылка: '', источник_документа: 'текст вставлен пользователем',
    },
    позиции: parsed.позиции,
    итог: tally(parsed.позиции),
    режим: 'живой',
  };
}
