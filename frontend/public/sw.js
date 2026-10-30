// Sahara AI (सहारा AI) PWA Service Worker
const CACHE_NAME = 'sahara-pwa-v3';
const ASSETS_TO_CACHE = [
  '/',
  '/app',
  '/senior/easy',
  '/coordinator/dashboard',
  '/manifest.json',
  '/favicon.ico',
  '/icon-192.png',
  '/icon-512.png',
  '/apple-touch-icon.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE).catch(() => {});
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
  if (event.request.method === 'GET') {
    event.respondWith(
      fetch(event.request).catch(() => {
        return caches.match(event.request);
      })
    );
  }
});

// Handle incoming check-in push notifications
self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : {};
  if (data.type === 'checkin_call' || data.type === 'direct_call') {
    const options = {
      body: data.title || 'सहारा AI इनकमिंग कॉल · बात करने के लिए टैप करें',
      icon: '/favicon.ico',
      badge: '/favicon.ico',
      vibrate: [300, 150, 300, 150, 300],
      tag: 'sahara-call',
      renotify: true,
      requireInteraction: true,
      data: {
        url: '/senior/easy'
      }
    };
    event.waitUntil(
      self.registration.showNotification('Sahara AI (सहारा AI)', options)
    );
  }
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow('/senior/easy')
  );
});
