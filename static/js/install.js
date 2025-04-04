let deferredPrompt = null;

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  console.log('✅ Evento beforeinstallprompt capturado');
  mostrarBotao();
});

document.addEventListener('DOMContentLoaded', () => {
  if (deferredPrompt) mostrarBotao();
});

function mostrarBotao() {
  const btn = document.getElementById('installBtn');
  if (btn) btn.style.display = 'block';
}

function installApp() {
  if (!deferredPrompt) return;
  deferredPrompt.prompt();
  deferredPrompt.userChoice.then((choiceResult) => {
    if (choiceResult.outcome === 'accepted') {
      console.log('App instalado');
    }
    deferredPrompt = null;
    document.getElementById('installBtn').style.display = 'none';
  });
}