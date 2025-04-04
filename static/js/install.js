let deferredPrompt = null;

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  console.log('✅ Evento beforeinstallprompt capturado');

  // Se o DOM já estiver carregado, mostra o botão
  if (document.readyState === 'complete') {
    mostrarBotao();
  } else {
    window.addEventListener('DOMContentLoaded', mostrarBotao);
  }
});

function mostrarBotao() {
  const installBtn = document.getElementById('installBtn');
  if (deferredPrompt && installBtn) {
    installBtn.style.display = 'block';
  }
}

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

window.installApp = installApp;
