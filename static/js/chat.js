// IIFE para encapsular o código e evitar poluir o escopo global
(function() {
    'use strict'; // Habilita modo estrito para pegar erros comuns

    // Cache de elementos DOM frequentemente usados
    let chatBox, messageInput, messageForm, sendBtn, claraStatusElement, 
        profilePic, modal, modalImg, closeModalBtn,
        emojiBtn, emojiPicker,
        deferredInstallPrompt = null; // Variável para PWA Install Prompt

    // --- INICIALIZAÇÃO ---
    function init() {
        // Seleciona os elementos DOM essenciais uma vez
        chatBox = document.getElementById("chat-box");
        messageInput = document.getElementById("mensagem");
        messageForm = document.getElementById("mensagem-form");
        sendBtn = document.querySelector('.send-btn');
        claraStatusElement = document.getElementById("clara-status");
        profilePic = document.getElementById("profile-pic");
        modal = document.getElementById("modal");
        modalImg = document.getElementById("modal-img");
        closeModalBtn = document.querySelector(".modal .close"); 
        emojiBtn = document.querySelector('.emoji-btn'); 
        const installButton = document.getElementById('install-app-button'); // <<< ADICIONADO Seleção do botão Instalar >>>

        // Verifica se os elementos essenciais existem
        if (!chatBox || !messageInput || !messageForm || !sendBtn || !claraStatusElement) {
             console.error("Erro: Elementos essenciais do chat não foram encontrados no DOM.");
             return; 
        }

        // Registra o Service Worker
        if ('serviceWorker' in navigator) {
          navigator.serviceWorker.register("{{ url_for('static', filename='sw.js') }}") // Ou '/static/sw.js'
            .then((registration) => { console.log('Service Worker: Registrado com sucesso:', registration.scope); })
            .catch((error) => { console.error('Service Worker: Falha no registro:', error); });
        } else {
          console.warn('Service Worker: Não suportado.');
        }
        
        // Adiciona listeners do formulário, input e botões
        messageForm.addEventListener("submit", sendMessage);
        messageInput.addEventListener("input", updateSendButton);
        messageInput.addEventListener("keypress", handleEnterKey);
        updateSendButton(); 
        if (emojiBtn) { emojiBtn.addEventListener('click', toggleEmojiPicker); } 
        else { console.warn("Botão emoji não encontrado."); }
        if (profilePic && modal && modalImg && closeModalBtn) {
             profilePic.addEventListener("click", openProfileModal);
             closeModalBtn.addEventListener("click", closeProfileModal);
             modal.addEventListener("click", (event) => { if (event.target === modal) closeProfileModal(); });
        } else { console.warn("Elementos do modal não encontrados."); }
        
        // --- <<< ADICIONADO Listener para o botão Instalar App >>> ---
        if (installButton) {
            installButton.addEventListener('click', handleInstallClick);
            console.log('[PWA] Listener de clique adicionado ao botão Instalar.');
        } else {
            console.warn('[PWA] Botão de Instalação (#install-app-button) não encontrado no HTML.');
        }
        // --- <<< FIM do Listener Instalar App >>> ---

        // Ajustes de layout
        window.addEventListener('resize', adjustChatHeight);
        adjustChatHeight(); 

        // Foco inicial
        messageInput.focus(); 
    }

    // --- FUNÇÕES DE UTILIDADE --- 
    // (getUserId, formatTime, scrollToBottom, setTypingStatus, updateSendButton, adjustChatHeight - mantidos)
    function getUserId() { /* ...código mantido... */  let userId = localStorage.getItem('user_id'); if (!userId) { userId = 'user-' + Date.now().toString(36) + Math.random().toString(36).substring(2, 7); try { localStorage.setItem('user_id', userId); } catch (e) { console.error("LS Error:", e); return 'user-temp-' + Date.now().toString(36); } } return userId; }
    function formatTime(date = new Date()) { /* ...código mantido... */  try { return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', hour12: false }); } catch (e) { const h = String(date.getHours()).padStart(2, '0'); const m = String(date.getMinutes()).padStart(2, '0'); return `${h}:${m}`; } }
    function scrollToBottom() { /* ...código mantido... */  if (chatBox) { chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: 'auto' }); } }
    function setTypingStatus(isTyping) { /* ...código mantido... */  if (claraStatusElement) { claraStatusElement.classList.toggle('typing', isTyping); claraStatusElement.textContent = isTyping ? "digitando..." : "online"; } }
    function updateSendButton() { /* ...código mantido... */  if (!sendBtn || !messageInput) return; if (messageInput.value.trim().length > 0) { sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>'; } else { sendBtn.innerHTML = '<i class="fas fa-microphone"></i>'; } }
    function adjustChatHeight() { /* ...código mantido... */  const header = document.querySelector('header'); const inputContainer = document.querySelector('.input-container'); if (header && inputContainer && chatBox) { const hH = header.offsetHeight; const iH = inputContainer.offsetHeight; chatBox.style.height = `calc(100vh - ${hH}px - ${iH}px)`; } }

    // --- LÓGICA PRINCIPAL DO CHAT --- 
    // (displayMessage, sendMessage - mantidos)
    function displayMessage(message) { /* ...código mantido... */   if (!chatBox || !message.text) return; const mD = document.createElement("div"); mD.className = `message ${message.from}`; const cD = document.createElement("div"); cD.className = "message-content"; cD.textContent = message.text; cD.style.whiteSpace = 'pre-wrap'; cD.style.wordBreak = 'break-word'; mD.appendChild(cD); const fD = document.createElement("div"); fD.className = "message-footer"; const tS = document.createElement("span"); tS.className = "timestamp"; tS.textContent = formatTime(); fD.appendChild(tS); if (message.from === "me") { const cS = document.createElement("span"); cS.className = "checkmarks"; cS.innerHTML = '<i class="fas fa-check"></i>'; fD.appendChild(cS); const cSFT = cS; setTimeout(() => { if (cSFT && chatBox.contains(cSFT)) { cSFT.innerHTML = '<i class="fas fa-check-double"></i>'; cSFT.classList.add('read'); } }, 1500 + Math.random() * 1000); } mD.appendChild(fD); chatBox.appendChild(mD); scrollToBottom();  }
    async function sendMessage(event) { /* ...código mantido... */  if (event) event.preventDefault(); if (!messageInput) return; const msg = messageInput.value.trim(); if (msg === "") return; const uId = getUserId(); displayMessage({ from: "me", text: msg }); messageInput.value = ""; updateSendButton(); messageInput.blur(); setTypingStatus(true); try { const rsp = await fetch("/clara", { method: "POST", headers: { "Content-Type": "application/json", }, body: JSON.stringify({ mensagem: msg, user_id: uId }) }); if (!rsp.ok) { let eD = rsp.statusText; try { const eDt = await rsp.json(); eD = eDt.error || eDt.message || eD; } catch (e) {} throw new Error(`Erro ${rsp.status}: ${eD}`); } const data = await rsp.json(); displayMessage({ from: "her", text: data.resposta || "Hmm..." }); } catch (err) { console.error("Falha API:", err); displayMessage({ from: "her", text: `⚠️ Ops! ${err.message || "..."}` }); } finally { setTypingStatus(false); } }

    // --- FUNÇÕES DO EMOJI PICKER ---
    // (toggleEmojiPicker, closeEmojiPicker, handleEmojiSelection, handleClickOutsidePicker - mantidos)
    function toggleEmojiPicker() { /* ...código mantido... */   if (!emojiPicker) { console.log("Criando emoji picker..."); emojiPicker = document.createElement('emoji-picker'); emojiPicker.style.position = 'absolute'; emojiPicker.style.bottom = '60px'; emojiPicker.style.left = '10px'; emojiPicker.style.zIndex = '1100'; emojiPicker.classList.add('light'); document.body.appendChild(emojiPicker); emojiPicker.addEventListener('emoji-click', handleEmojiSelection); setTimeout(() => { document.addEventListener('click', handleClickOutsidePicker, { capture: true, once: true }); }, 0); } else { console.log("Fechando emoji picker..."); closeEmojiPicker(); } }
    function closeEmojiPicker() { /* ...código mantido... */   if (emojiPicker) { emojiPicker.removeEventListener('emoji-click', handleEmojiSelection); if (document.body.contains(emojiPicker)) { document.body.removeChild(emojiPicker); } emojiPicker = null; document.removeEventListener('click', handleClickOutsidePicker, { capture: true }); console.log("Emoji picker fechado."); } }
    function handleEmojiSelection(event) { /* ...código mantido... */  console.log("Emoji selecionado:", event.detail); if (!messageInput) return; const emj = event.detail.unicode; const pos = messageInput.selectionStart; const txtB = messageInput.value.substring(0, pos); const txtA = messageInput.value.substring(pos); messageInput.value = txtB + emj + txtA; const nPos = pos + emj.length; messageInput.selectionStart = nPos; messageInput.selectionEnd = nPos; messageInput.focus(); updateSendButton(); /* closeEmojiPicker(); */  }
    function handleClickOutsidePicker(event) { /* ...código mantido... */   if (emojiPicker && !emojiPicker.contains(event.target) && emojiBtn && !emojiBtn.contains(event.target)) { console.log("Clique fora detectado."); closeEmojiPicker(); } else if (emojiPicker) { document.addEventListener('click', handleClickOutsidePicker, { capture: true, once: true }); } }

    // --- HANDLERS DE EVENTOS ADICIONAIS --- 
    // (handleEnterKey, openProfileModal, closeProfileModal - mantidos)
    function handleEnterKey(event) { /* ...código mantido... */  if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); if (messageForm) { messageForm.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true })); } } }
    function openProfileModal() { /* ...código mantido... */  if (modal && modalImg && profilePic) { modalImg.src = profilePic.src; modal.style.display = "flex"; } }
    function closeProfileModal() { /* ...código mantido... */  if (modal) { modal.style.display = "none"; } }

    // --- LÓGICA PWA INSTALL PROMPT ---

    // Listener para Capturar Evento de Instalação (Modificado para mostrar o botão)
    window.addEventListener('beforeinstallprompt', (event) => {
      console.log('[PWA] Evento beforeinstallprompt capturado!');
      event.preventDefault(); 
      deferredInstallPrompt = event; 
      console.log('[PWA] Prompt de instalação guardado.');
      
      // --- <<< ADICIONADO Lógica para mostrar o botão >>> ---
      const installButton = document.getElementById('install-app-button');
      if (installButton) {
          console.log('[PWA] Tornando o botão de instalação visível.');
          installButton.style.display = 'inline-block'; // Ou 'block'
      }
      // --- <<< FIM da Lógica para mostrar o botão >>> ---
    });

    // Função para Disparar Instalação (Já estava aqui)
    async function handleInstallClick() {
      console.log('[PWA] Botão Instalar clicado.');
      const installButton = document.getElementById('install-app-button'); 

      if (deferredInstallPrompt) { 
        deferredInstallPrompt.prompt(); 
        const { outcome } = await deferredInstallPrompt.userChoice;
        console.log(`[PWA] Resultado da instalação: ${outcome}`); 
        deferredInstallPrompt = null; 
        if (installButton) {
          installButton.style.display = 'none'; 
          console.log('[PWA] Botão de instalação escondido após uso.');
        }
      } else {
        console.log('[PWA] Nenhum prompt de instalação para mostrar.');
        if (installButton) installButton.style.display = 'none'; 
      }
    }


    // --- INICIALIZAÇÃO DO SCRIPT ---
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init(); 
    }

})(); // Fim da IIFE