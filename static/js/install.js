let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  const installBtn = document.getElementById('installBtn');
  if (installBtn) {
    installBtn.style.display = 'block';
  }
});

function installApp() {
  if (!deferredPrompt) return;

  deferredPrompt.prompt();

  deferredPrompt.userChoice.then((choiceResult) => {
    if (choiceResult.outcome === 'accepted') {
      console.log('Usuário aceitou instalar');
    } else {
      console.log('Usuário recusou instalar');
    }
    deferredPrompt = null;
    document.getElementById('installBtn').style.display = 'none';
  });
}
