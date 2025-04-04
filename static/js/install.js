let deferredPrompt = null;

// Captura o evento disparado quando o app é instalável
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  console.log('✅ Evento beforeinstallprompt capturado');

  // Mostra o botão se o DOM já estiver carregado
  if (document.readyState === 'complete') {
    mostrarBotaoInstalacaoSeDisponivel();
  } else {
    window.addEventListener('DOMContentLoaded', mostrarBotaoInstalacaoSeDisponivel);
  }
});

// Mostra o botão de instalação se as condições forem atendidas
function mostrarBotaoInstalacaoSeDisponivel() {
  const installBtn = document.getElementById('installBtn');
  if (deferredPrompt && installBtn) {
    installBtn.style.display = 'block';
    console.log('📲 Botão de instalação exibido');
  }
}

// Executa a instalação ao clicar no botão
function installApp() {
  if (!deferredPrompt) return;

  deferredPrompt.prompt();

  deferredPrompt.userChoice.then((choiceResult) => {
    if (choiceResult.outcome === 'accepted') {
      console.log('👍 Usuário aceitou instalar');
    } else {
      console.log('👎 Usuário recusou instalar');
    }

    deferredPrompt = null;
    document.getElementById('installBtn').style.display = 'none';
  });
}

// Expor função no escopo global (HTML usa no onclick)
window.installApp = installApp;
