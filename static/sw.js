// static/sw.js - Service Worker Básico

self.addEventListener('install', (event) => {
    console.log('Service Worker: Instalado');
    // self.skipWaiting(); // Descomente se quiser que o SW ative imediatamente após instalar
  });
  
  self.addEventListener('activate', (event) => {
    console.log('Service Worker: Ativado');
    // event.waitUntil(clients.claim()); // Garante controle imediato das páginas abertas
  });
  
  self.addEventListener('fetch', (event) => {
    // Por enquanto, não faz nada com as requisições, apenas deixa passar.
    // console.log('Service Worker: Fetching', event.request.url);
    // event.respondWith(fetch(event.request)); // Comportamento padrão de rede
  });