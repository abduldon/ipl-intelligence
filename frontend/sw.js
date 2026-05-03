const CACHE_NAME = 'ipl-intelligence-v1';
const STATIC_ASSETS = [
  '/',
  '/login',
  '/static/index.html',
  '/static/login.html',
  '/static/manifest.json',
  'https://cdn.jsdelivr.net/npm/chart.js'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(STATIC_ASSETS).catch(err => {
        console.log('Cache install error:', err);
      });
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  // Don't cache API calls
  if (event.request.url.includes('/auth/') ||
      event.request.url.includes('/players/') ||
      event.request.url.includes('/teams/') ||
      event.request.url.includes('/auction/') ||
      event.request.url.includes('/squad/') ||
      event.request.url.includes('/export/')) {
    return fetch(event.request);
  }

  event.respondWith(
    caches.match(event.request).then(cached => {
      return cached || fetch(event.request).then(response => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      }).catch(() => cached);
    })
  );
});