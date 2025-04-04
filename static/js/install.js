let deferredPrompt = null;

// Captura o evento disparado pelo navegador quando o app é "instalável"
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  console.log('✅ Evento beforeinstallprompt capturado');
});

// Mostra o botão de instalação se o evento foi capturado
function mostrarBotaoInstalacaoSeDisponivel() {
  const installBtn = document.getElementById('installBtn');
  if (deferredPrompt && installBtn) {
    installBtn.style.display = 'block';
  }
}

// Executa a instalação quando o botão for clicado
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

// Disponibiliza as funções no escopo global
window.mostrarBotaoInstalacaoSeDisponivel = mostrarBotaoInstalacaoSeDisponivel;
window.installApp = installApp;
