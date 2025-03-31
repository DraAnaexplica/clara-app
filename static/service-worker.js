// Service Worker da Clara

self.addEventListener("install", function (event) {
    console.log("✅ Service Worker instalado.");
    self.skipWaiting(); // Força ativação imediata
  });
  
  self.addEventListener("activate", function (event) {
    console.log("✅ Service Worker ativado.");
  });
  
  self.addEventListener("fetch", function (event) {
    // Aqui deixamos todas as requisições passarem normalmente
  });
  