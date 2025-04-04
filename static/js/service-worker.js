self.addEventListener('install', (event) => {
    console.log('[ServiceWorker] Installed');
  });
  
  self.addEventListener('fetch', (event) => {
    // Padrão: apenas passa requisições adiante
    event.respondWith(fetch(event.request));
  });
  