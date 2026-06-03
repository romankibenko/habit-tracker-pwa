/**
 * Service Worker для PWA.
 *
 * Стратегии:
 *  - статика приложения (HTML, CSS, JS, иконки, manifest) — cache-first
 *    с фоновым обновлением (stale-while-revalidate в простой форме);
 *  - API-запросы (/api/*) — network-only, чтобы не отдавать устаревшие данные;
 *  - офлайн-фоллбек на закешированный index.html.
 *
 * Push-обработчик показывает уведомление и кликом открывает приложение.
 */

const CACHE_VERSION = 'habit-tracker-v1';

const PRECACHE = [
  '/',
  '/manifest.json',
  '/static/css/style.css',
  '/static/js/app.js',
  '/static/js/api.js',
  '/static/js/auth.js',
  '/static/js/habits.js',
  '/static/js/stats.js',
  '/static/js/push.js',
  '/static/js/install.js',
  '/static/js/toast.js',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => cache.addAll(PRECACHE))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((key) => key !== CACHE_VERSION).map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // API: всегда из сети, кеш не используем
  if (url.pathname.startsWith('/api/')) return;

  // Навигация на HTML: network-first → fallback к закешированному /
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).catch(() => caches.match('/'))
    );
    return;
  }

  // Статика: cache-first + фоновое обновление
  event.respondWith(
    caches.match(request).then((cached) => {
      const fetchPromise = fetch(request)
        .then((response) => {
          if (response && response.status === 200 && response.type === 'basic') {
            const clone = response.clone();
            caches.open(CACHE_VERSION).then((cache) => cache.put(request, clone));
          }
          return response;
        })
        .catch(() => cached);
      return cached || fetchPromise;
    })
  );
});

// ============ Web Push ============

self.addEventListener('push', (event) => {
  let data = { title: 'Habit Tracker', body: 'У тебя уведомление' };
  try {
    if (event.data) data = { ...data, ...event.data.json() };
  } catch (_) {
    // payload не JSON — ок, используем дефолт
  }
  const options = {
    body: data.body,
    icon: '/static/icons/icon-192.png',
    badge: '/static/icons/icon-192.png',
    data: { url: data.url || '/' },
  };
  event.waitUntil(self.registration.showNotification(data.title, options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = event.notification.data?.url || '/';
  event.waitUntil(
    self.clients.matchAll({ type: 'window' }).then((clients) => {
      for (const client of clients) {
        if (client.url.includes(url) && 'focus' in client) return client.focus();
      }
      return self.clients.openWindow(url);
    })
  );
});
