// Respiración Pro - Service Worker v5.0 (rediseño papel y tinta + voz grabada)
// Solo se usa si la app se abre desde la web; dentro de la app de Android no se registra.
const CACHE_NAME = 'respiracion-pro-v5.0';
const OFFLINE_URL = './index.html';

// Archivos a cachear para funcionamiento offline
const ASSETS_TO_CACHE = [
  './',
  './index.html',
  './privacy.html',
  './manifest.json',
  './icons/icon-72.png',
  './icons/icon-96.png',
  './icons/icon-128.png',
  './icons/icon-144.png',
  './icons/icon-152.png',
  './icons/icon-192.png',
  './icons/icon-384.png',
  './icons/icon-512.png',
  './icons/icon-maskable-192.png',
  './icons/icon-maskable-512.png',
  './fonts/eb-garamond-latin-400-normal.woff2',
  './fonts/eb-garamond-latin-400-italic.woff2',
  './fonts/eb-garamond-latin-500-normal.woff2',
  './img/papel.webp',
  './img/tinta.webp',
  './img/enso-papel.webp',
  './img/enso-tinta.webp',
  './img/aguada-papel.webp',
  './img/aguada-tinta.webp',
  './audio/voz/es/ready.ogg',
  './audio/voz/es/inhale.ogg',
  './audio/voz/es/hold.ogg',
  './audio/voz/es/exhale.ogg',
  './audio/voz/es/rest.ogg',
  './audio/voz/es/done.ogg',
  './audio/voz/en/ready.ogg',
  './audio/voz/en/inhale.ogg',
  './audio/voz/en/hold.ogg',
  './audio/voz/en/exhale.ogg',
  './audio/voz/en/rest.ogg',
  './audio/voz/en/done.ogg',
  './audio/voz/de/ready.ogg',
  './audio/voz/de/inhale.ogg',
  './audio/voz/de/hold.ogg',
  './audio/voz/de/exhale.ogg',
  './audio/voz/de/rest.ogg',
  './audio/voz/de/done.ogg'
];

// Instalación del Service Worker
self.addEventListener('install', (event) => {
  console.log('[SW] Instalando Service Worker...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Cacheando archivos de la app...');
        return cache.addAll(ASSETS_TO_CACHE);
      })
      .then(() => {
        console.log('[SW] Todos los archivos cacheados');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[SW] Error durante la instalación:', error);
      })
  );
});

// Activación del Service Worker
self.addEventListener('activate', (event) => {
  console.log('[SW] Activando Service Worker...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((cacheName) => cacheName !== CACHE_NAME)
            .map((cacheName) => {
              console.log('[SW] Eliminando caché antigua:', cacheName);
              return caches.delete(cacheName);
            })
        );
      })
      .then(() => {
        console.log('[SW] Service Worker activado');
        return self.clients.claim();
      })
  );
});

// Estrategia de caché: Network First con fallback a Cache
self.addEventListener('fetch', (event) => {
  // Solo manejar peticiones GET
  if (event.request.method !== 'GET') {
    return;
  }

  // Ignorar peticiones de extensiones de Chrome
  if (event.request.url.startsWith('chrome-extension://')) {
    return;
  }

  event.respondWith(
    // Intentar red primero
    fetch(event.request)
      .then((response) => {
        // Si la respuesta es válida, guardarla en caché
        if (response && response.status === 200) {
          const responseToCache = response.clone();
          caches.open(CACHE_NAME)
            .then((cache) => {
              cache.put(event.request, responseToCache);
            });
        }
        return response;
      })
      .catch(() => {
        // Si falla la red, buscar en caché
        return caches.match(event.request)
          .then((cachedResponse) => {
            if (cachedResponse) {
              return cachedResponse;
            }
            
            // Si no está en caché y es una navegación, devolver página offline
            if (event.request.mode === 'navigate') {
              return caches.match(OFFLINE_URL);
            }
            
            // Para otros recursos, devolver error genérico
            return new Response('Recurso no disponible offline', {
              status: 503,
              statusText: 'Service Unavailable'
            });
          });
      })
  );
});

// Manejar mensajes del cliente
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

console.log('[SW] Service Worker cargado');
