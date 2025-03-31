self.addEventListener("install", (event) => {
    console.log("🛠️ Service Worker instalado");
    self.skipWaiting(); // Força ativação imediata
  });
  
  self.addEventListener("activate", (event) => {
    console.log("🚀 Service Worker ativado");
  });
  
  self.addEventListener("fetch", (event) => {
    // Apenas deixa passar todas as requisições (sem cache ainda)
  });
  