/// <reference types="vite/client" />
interface ImportMetaEnv {
  /** Ключ Claude API для «живого» режима. Только для локального теста: в собранном сайте ключ виден всем. */
  readonly VITE_ANTHROPIC_API_KEY?: string;
}
interface ImportMeta {
  readonly env: ImportMetaEnv;
}
