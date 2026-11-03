// localStorage всегда в try/catch: в приватном окне и при заблокированных данных сайта он бросает ошибку.
export function lsGet(key: string): string | null {
  try { return window.localStorage.getItem(key); } catch { return null; }
}
export function lsSet(key: string, value: string): boolean {
  try { window.localStorage.setItem(key, value); return true; } catch { return false; }
}
export function lsRemove(key: string): void {
  try { window.localStorage.removeItem(key); } catch { /* нечего делать */ }
}
