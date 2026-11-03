// Собирает src/fonts.css из пакетов @fontsource: только кириллица и латиница, только woff2.
// Так шрифты встраиваются в собранный сайт и он открывается без интернета.
import { readFileSync, writeFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const faces = [
  ['old-standard-tt', ['400', '700', '400-italic']],
  ['pt-serif', ['400', '700', '400-italic']],
  ['ibm-plex-sans', ['400', '500', '600']],
  ['ibm-plex-mono', ['400', '500']],
];
let out = '/* Создано scripts/build_fonts_css.mjs — шрифты @fontsource (SIL OFL), кириллица + латиница */\n';
for (const [pkg, weights] of faces) {
  for (const w of weights) {
    const css = readFileSync(join(root, 'node_modules/@fontsource', pkg, `${w}.css`), 'utf8');
    const blocks = css.split('@font-face').slice(1);
    for (const b of blocks) {
      const subset = /\/\* [\w-]+-(cyrillic|latin)-\d+-(?:normal|italic) \*\//.exec('/*' + b.split('/*')[0]);
      const m = /\/\* ([\w-]+) \*\//.exec(css.slice(css.indexOf(b) - 80, css.indexOf(b)));
      const name = m ? m[1] : '';
      // latin-ext нужен ради знака рубля ₽ (U+20BD) — берём его для шрифтов интерфейса и текста.
      const wantExt = pkg !== 'old-standard-tt' && !w.includes('italic');
      const re = wantExt ? /-(cyrillic|latin|latin-ext)-\d+-(normal|italic)$/ : /-(cyrillic|latin)-\d+-(normal|italic)$/;
      if (!re.test(name) || /cyrillic-ext/.test(name)) continue;
      const body = b.replace(/url\(\.\/files\/([^)]+\.woff2)\) format\('woff2'\), url\([^)]+\.woff\) format\('woff'\)/,
        (_, f) => `url('../node_modules/@fontsource/${pkg}/files/${f}') format('woff2')`);
      out += `/* ${name} */\n@font-face${body.split('/*')[0].trimEnd()}\n`;
      void subset;
    }
  }
}
writeFileSync(join(root, 'src/fonts.css'), out);
console.log('fonts.css:', (out.match(/@font-face/g) || []).length, 'faces');
