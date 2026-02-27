// Service Worker para cache offline básico
const CACHE_NAME = 'checklist-veicular-v1.0';
const STATIC_CACHE = 'checklist-static-v1.0';

// Assets para cache estático
const STATIC_ASSETS = [
  '/',
  '/static/css/styles.css',
  '/static/js/icons.js',
  '/static/js/service-worker.js',
  // Adicionar outros assets estáticos conforme necessário
];

// Cache primeiro, depois rede (para assets estáticos)
self.addEventListener('install', (event) => {
  console.log('[SW] Install');
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .catch((error) => {
        console.error('[SW] Cache install failed:', error);
      })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  console.log('[SW] Activate');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== STATIC_CACHE && cacheName !== CACHE_NAME) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  // Estratégia: Cache First para assets estáticos, Network First para dados dinâmicos
  const url = new URL(event.request.url);

  if (event.request.method !== 'GET') return;

  // Para assets estáticos (CSS, JS, imagens estáticas)
  if (url.pathname.startsWith('/static/') ||
      url.pathname.includes('.css') ||
      url.pathname.includes('.js') ||
      url.pathname.includes('.png') ||
      url.pathname.includes('.jpg') ||
      url.pathname.includes('.jpeg') ||
      url.pathname.includes('.svg') ||
      url.pathname.includes('.ico')) {

    event.respondWith(
      caches.match(event.request)
        .then((response) => {
          if (response) {
            return response;
          }
          return fetch(event.request).then((response) => {
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            const responseToCache = response.clone();
            caches.open(STATIC_CACHE)
              .then((cache) => {
                cache.put(event.request, responseToCache);
              });
            return response;
          });
        })
    );
  } else {
    // Para outras requisições, tentar rede primeiro, depois cache
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          // Cache successful responses
          if (response.status === 200) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME)
              .then((cache) => {
                cache.put(event.request, responseClone);
              });
          }
          return response;
        })
        .catch(() => {
          // Fallback to cache
          return caches.match(event.request)
            .then((response) => {
              if (response) {
                return response;
              }
              // Fallback para página offline se disponível
              if (event.request.destination === 'document') {
                return caches.match('/offline.html');
              }
            });
        })
    );
  }
});

// Limpeza periódica de cache
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'CLEAN_CACHE') {
    cleanOldCache();
  }
});

function cleanOldCache() {
  const maxAge = 24 * 60 * 60 * 1000; // 24 horas
  caches.open(CACHE_NAME).then((cache) => {
    cache.keys().then((keys) => {
      keys.forEach((request) => {
        // Verificar se o cache é muito antigo
        // Nota: Isso é uma simplificação, uma implementação real precisaria de timestamps
      });
    });
  });
}

// Sincronização em background (se suportado)
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

function doBackgroundSync() {
  // Implementar sincronização em background se necessário
  console.log('[SW] Background sync triggered');
}
