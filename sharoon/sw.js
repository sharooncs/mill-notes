// Mill Notes service worker — app shell cached for full offline use.
const VERSION = 'v6';
const CACHE = 'millnotes-' + VERSION;
const SHELL = ['./', './index.html', './manifest.webmanifest', './icon-180.png', './icon-512.png', './icon-512-maskable.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL.map((u) => new Request(u, { cache: 'reload' })))).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;
  // App shell: cache first, then network, and refresh the cache in the background.
  e.respondWith(
    caches.match(req, { ignoreSearch: true }).then((hit) => {
      const fetching = fetch(req).then((res) => {
        if (res && res.ok) caches.open(CACHE).then((c) => c.put(req, res.clone()));
        return res;
      }).catch(() => hit || caches.match('./index.html'));
      return hit || fetching;
    })
  );
});

self.addEventListener('message', (e) => { if (e.data === 'skipWaiting') self.skipWaiting(); });
