// Маршруты на «#» (hash-роутинг): сайт работает из файла и на любом статическом хостинге,
// сервер не нужен. Адреса: #/ , #/demo/assortiment , #/demo/tendery , #/demo/tender/<id> ,
// #/demo/zayavka/<id> , #/demo/sroki/<id>

import { useEffect, useState } from 'react';

export function currentPath(): string {
  const h = window.location.hash.replace(/^#/, '');
  return h.startsWith('/') ? h : '/' + h;
}

export function useRoute(): { path: string; parts: string[] } {
  const [path, setPath] = useState(currentPath);
  useEffect(() => {
    const on = () => {
      setPath(currentPath());
      // Новый экран — с начала страницы (кроме переходов внутри страницы)
      window.scrollTo({ top: 0 });
    };
    window.addEventListener('hashchange', on);
    return () => window.removeEventListener('hashchange', on);
  }, []);
  const clean = path.split('?')[0];
  return { path: clean, parts: clean.split('/').filter(Boolean).map((p) => decodeURIComponent(p)) };
}

export function go(to: string) {
  window.location.hash = to.startsWith('#') ? to : '#' + to;
}

export const href = (to: string) => '#' + to;
