let deferredPrompt = null;

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  console.log('✅ beforeinstallprompt capturado');

  // Mostrar automaticamente ao entrar no app
  mostrarBotaoInstalacao();
});

// Garante exibição mesmo se o DOM ainda não estiver pronto
document.addEventListener('DOMContentLoaded', () => {
  if (deferredPrompt) {
    mostrarBotaoInstalacao();
  }
});

function mostrarBotaoInstalacao() {
  const btn = document.getElementById('installBtn');
  if (btn) {
    btn.style.display = 'block';
    console.log('📲 Botão de instalação exibido');
  }
}

function installApp() {
  if (!deferredPrompt) return;

  deferredPrompt.prompt();

  deferredPrompt.userChoice.then((choiceResult) => {
    if (choiceResult.outcome === 'accepted') {
      console.log('👍 App será instalado');
    } else {
      console.log('👎 Usuário recusou');
    }

    deferredPrompt = null;
    const btn = document.getElementById('installBtn');
    if (btn) btn.style.display = 'none';
  });
}

window.installApp = installApp;
