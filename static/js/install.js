let deferredPrompt;
const installBtn = document.getElementById('installBtn');

window.addEventListener('beforeinstallprompt', (e) => {
  console.log("✅ Evento beforeinstallprompt capturado");
  e.preventDefault();
  deferredPrompt = e;
  installBtn.style.display = 'block';

  installBtn.addEventListener('click', () => {
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then((choice) => {
      if (choice.outcome === 'accepted') {
        console.log("📲 Aplicativo instalado!");
      } else {
        console.log("❌ Instalação recusada.");
      }
      deferredPrompt = null;
    });
  });
});