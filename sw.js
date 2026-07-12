// Respiración Pro — service worker de limpieza (la web es ahora una landing estática).
// Se desinstala a sí mismo y borra las cachés antiguas de los visitantes que tenían la app web.
self.addEventListener('install', () => { self.skipWaiting(); });
self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.map(k => caches.delete(k)));
    await self.registration.unregister();
    const clients = await self.clients.matchAll({ type: 'window' });
    clients.forEach(c => c.navigate(c.url));
  })());
});
