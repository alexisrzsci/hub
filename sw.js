/* Alexis Hub service worker: works offline with the last saved app and board. */
const CACHE = "hub-v3";
const SHELL = ["./", "index.html", "manifest.webmanifest", "icon-180.png", "icon-192.png", "icon-512.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

async function networkFirst(req, key) {
  const c = await caches.open(CACHE);
  try {
    const res = await fetch(req);
    if (res.ok) c.put(key || req, res.clone());
    return res;
  } catch (err) {
    const hit = await c.match(key || req);
    if (hit) return hit;
    throw err;
  }
}
async function cacheFirst(req) {
  const c = await caches.open(CACHE);
  const hit = await c.match(req);
  if (hit) return hit;
  const res = await fetch(req);
  if (res.ok || res.type === "opaque") c.put(req, res.clone());
  return res;
}

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin === location.origin) {
    if (url.pathname.endsWith("data.enc.json")) { e.respondWith(networkFirst(req, "data.enc.json")); return; }
    if (req.mode === "navigate") { e.respondWith(networkFirst(req, "index.html")); return; }
    e.respondWith(networkFirst(req));
    return;
  }
  if (url.hostname === "fonts.googleapis.com" || url.hostname === "fonts.gstatic.com") { e.respondWith(cacheFirst(req)); return; }
});
