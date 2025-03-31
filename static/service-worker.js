self.addEventListener("install", function (event) {
    console.log("Service worker instalado.");
    self.skipWaiting();
  });
  
  self.addEventListener("activate", function (event) {
    console.log("Service worker ativado.");
  });
  
  self.addEventListener("fetch", function (event) {
    // Apenas deixa passar as requisições
  });
  