let deferredPrompt;
const installBtn = document.getElementById('installBtn');

window.addEventListener('beforeinstallprompt', (e) => {
  console.log("✅ Evento beforeinstallprompt capturado");
  e.preventDefault();
  deferredPrompt = e;
  installBtn.style.display = 'block';

  installBtn.addEventListener('click', () => {
    if (deferredPrompt) {
      deferredPrompt.prompt();
      deferredPrompt.userChoice.then((choiceResult) => {
        if (choiceResult.outcome === 'accepted') {
          console.log('📲 Usuário aceitou a instalação');
        } else {
          console.log('❌ Usuário recusou a instalação');
        }
        deferredPrompt = null;
      });
    }
  });
});