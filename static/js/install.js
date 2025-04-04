let deferredPrompt;
const installBtn = document.getElementById('installBtn');

// Banner de debug visual
const banner = document.createElement('div');
banner.id = 'debug-banner';
banner.style.position = 'fixed';
banner.style.bottom = '60px';
banner.style.left = '20px';
banner.style.background = '#222';
banner.style.color = '#0f0';
banner.style.padding = '10px';
banner.style.zIndex = 9999;
banner.style.fontSize = '14px';
banner.innerText = '⏳ Aguardando evento beforeinstallprompt...';
document.body.appendChild(banner);

window.addEventListener('beforeinstallprompt', (e) => {
  console.log("✅ Evento beforeinstallprompt capturado");
  banner.innerText = '✅ Evento beforeinstallprompt capturado! Botão habilitado.';
  e.preventDefault();
  deferredPrompt = e;
  installBtn.style.display = 'block';

  installBtn.addEventListener('click', () => {
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then((choice) => {
      if (choice.outcome === 'accepted') {
        banner.innerText = '📲 Aplicativo instalado com sucesso!';
        console.log("📲 Aplicativo instalado!");
      } else {
        banner.innerText = '❌ Usuário recusou a instalação';
        console.log("❌ Instalação recusada.");
      }
      deferredPrompt = null;
    });
  });
});

setTimeout(() => {
  if (!deferredPrompt) {
    banner.innerText = '⚠️ Evento beforeinstallprompt NÃO disparou. App pode já estar instalado ou navegador não suportado.';
    banner.style.color = '#ff0';
  }
}, 5000);