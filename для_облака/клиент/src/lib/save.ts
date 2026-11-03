// Сохранение файла у пользователя.
// Вне claude.ai — обычная blob-ссылка. На claude.ai прямые скачивания запрещены: файл отдаём через
// возможность `downloads` (просмотрщик спросит подтверждение). Определения: artifact-capabilities/downloads.d.ts.

type Downloads = { save: (r: { filename: string; data: Blob | string }) => Promise<{ status: string }> };
type ClaudeRuntime = { use: (name: string) => Promise<unknown> };

export function runtime(): ClaudeRuntime | null {
  const c = (window as unknown as { claude?: ClaudeRuntime }).claude;
  return c && typeof c.use === 'function' ? c : null;
}

let pending: Promise<Downloads | null> | null = null;
export function getDownloads(): Promise<Downloads | null> {
  const c = runtime();
  if (!c) return Promise.resolve(null);
  if (!pending) pending = c.use('downloads').then((d) => (d as Downloads | null) ?? null).catch(() => null);
  return pending;
}

function blobLink(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = name;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

export type SaveOutcome = 'saved' | 'declined' | 'failed';

export async function saveFile(blob: Blob, name: string): Promise<SaveOutcome> {
  if (runtime()) {
    const dl = await getDownloads();
    if (!dl) { blobLink(blob, name); return 'saved'; } // top-level копия страницы: обычная ссылка
    try { await dl.save({ filename: name, data: blob }); return 'saved'; }
    catch (e) { return (e as { code?: string })?.code === 'declined' ? 'declined' : 'failed'; }
  }
  blobLink(blob, name);
  return 'saved';
}
