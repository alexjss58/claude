// Сохранение файла у пользователя.
// Обычный браузер или файл, открытый с диска: скачивание через blob-ссылку.
// Страница опубликована на claude.ai (Artifact): там прямые скачивания запрещены, поэтому файл
// передаётся через разрешённый механизм `downloads` (просмотрщик спросит подтверждение).

type Downloads = { save: (r: { filename: string; data: Blob }) => Promise<{ status: string }> };
type ClaudeRuntime = { use: (name: string) => Promise<unknown> };

let pending: Promise<Downloads | null> | null = null;

function runtime(): ClaudeRuntime | null {
  const c = (window as unknown as { claude?: ClaudeRuntime }).claude;
  return c && typeof c.use === 'function' ? c : null;
}

/** null — страница открыта не в claude.ai или скачивания там недоступны */
export function getDownloads(): Promise<Downloads | null> {
  const c = runtime();
  if (!c) return Promise.resolve(null);
  if (!pending) pending = c.use('downloads').then((d) => (d as Downloads | null) ?? null).catch(() => null);
  return pending;
}

/** true — страница внутри claude.ai, где обычные ссылки на скачивание не работают */
export function insideClaude(): boolean {
  return runtime() !== null;
}

function blobLink(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

/** Отдать файл пользователю. Отказ пользователя в окне подтверждения — не ошибка. */
export async function saveFile(blob: Blob, name: string): Promise<void> {
  const dl = await getDownloads();
  if (dl) {
    try {
      await dl.save({ filename: name, data: blob });
    } catch (e) {
      const code = (e as { code?: string })?.code;
      if (code !== 'declined' && code !== 'rate_limited') {
        alert('Скачать файл здесь не получилось. Откройте прототип как файл на компьютере.');
      }
    }
    return;
  }
  blobLink(blob, name);
}

/** Скачать файл, лежащий рядом со страницей (пример прайса, демо-каталог). */
export async function saveStatic(path: string, name: string): Promise<boolean> {
  if (!insideClaude()) return false; // вне claude.ai работает обычная ссылка
  try {
    const res = await fetch(path);
    if (!res.ok) throw new Error(String(res.status));
    await saveFile(await res.blob(), name);
  } catch {
    alert('Файл здесь недоступен. Откройте прототип как файл на компьютере.');
  }
  return true;
}

// Заранее спрашиваем доступность: ответ приходит позже, первый клик не ждёт.
if (typeof window !== 'undefined') void getDownloads();
