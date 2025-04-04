// IIFE para encapsular o código e evitar poluir o escopo global
(function() {
    'use strict'; // Habilita modo estrito para pegar erros comuns

    // Cache de elementos DOM frequentemente usados
    let chatBox, messageInput, messageForm, sendBtn, claraStatusElement, 
        profilePic, modal, modalImg, closeModalBtn,
        emojiBtn, emojiPicker; // <<< ADICIONADO Variáveis para emoji >>>

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
        emojiBtn = document.querySelector('.emoji-btn'); // <<< ADICIONADO Seleção do botão emoji >>>

        // Verifica se os elementos essenciais do formulário/chat existem
        if (!chatBox || !messageInput || !messageForm || !sendBtn || !claraStatusElement) {
             console.error("Erro: Elementos essenciais do chat não foram encontrados no DOM.");
             return; // Interrompe a inicialização se algo crítico faltar
        }
        
        // Adiciona listeners do formulário e input
        messageForm.addEventListener("submit", sendMessage);
        messageInput.addEventListener("input", updateSendButton);
        messageInput.addEventListener("keypress", handleEnterKey);
        updateSendButton(); // Define o estado inicial do botão (microfone)

        // Adiciona listener para o botão de emoji (SE ele existir)
        // vv ADICIONADO Listener para o botão emoji vv
        if (emojiBtn) {
            emojiBtn.addEventListener('click', toggleEmojiPicker);
        } else {
            console.warn("Botão de emoji (.emoji-btn) não encontrado.");
        }
        // ^^ FIM do listener do botão emoji ^^

        // Adiciona listeners do modal de perfil (se existir)
        if (profilePic && modal && modalImg && closeModalBtn) {
             profilePic.addEventListener("click", openProfileModal);
             closeModalBtn.addEventListener("click", closeProfileModal);
             // Fecha modal se clicar no fundo escuro
             modal.addEventListener("click", function(event) {
                if (event.target === modal) {
                    closeProfileModal();
                }
             });
        } else {
            console.warn("Elementos do modal não encontrados. Funcionalidade de clique na foto desativada.");
        }
        
        // Ajustes de layout na inicialização e em resize
        window.addEventListener('resize', adjustChatHeight);
        adjustChatHeight(); // Ajusta altura inicial

        // Foco inicial no input (bom para desktop)
        messageInput.focus(); 
    }

    // --- FUNÇÕES DE UTILIDADE --- (getUserId, formatTime, scrollToBottom, etc. - mantidas como antes)

    // Gera ou recupera um ID de usuário único (localStorage)
    function getUserId() {
        let userId = localStorage.getItem('user_id');
        if (!userId) {
            userId = 'user-' + Date.now().toString(36) + Math.random().toString(36).substring(2, 7);
            try {
                localStorage.setItem('user_id', userId);
            } catch (e) {
                console.error("Não foi possível salvar user_id no localStorage:", e);
                return 'user-temp-' + Date.now().toString(36); 
            }
        }
        return userId;
    }

    // Formata a hora atual para HH:MM (formato 24h)
    function formatTime(date = new Date()) {
        try {
            return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', hour12: false });
        } catch (e) {
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            return `${hours}:${minutes}`;
        }
    }

    // Rola a área de chat para a última mensagem
    function scrollToBottom() {
        if (chatBox) {
            chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: 'auto' }); 
        }
    }

    // Atualiza o status da Clara (online/digitando)
    function setTypingStatus(isTyping) {
        if (claraStatusElement) {
            claraStatusElement.classList.toggle('typing', isTyping); 
            claraStatusElement.textContent = isTyping ? "digitando..." : "online"; 
        }
    }

    // Atualiza o ícone do botão Enviar/Microfone
    function updateSendButton() {
        if (!sendBtn || !messageInput) return; 

        if (messageInput.value.trim().length > 0) {
            sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>'; // Ícone Enviar
        } else {
            sendBtn.innerHTML = '<i class="fas fa-microphone"></i>'; // Ícone Microfone
        }
    }
    
    // Ajusta a altura da área de chat dinamicamente
    function adjustChatHeight() {
        const header = document.querySelector('header'); 
        const inputContainer = document.querySelector('.input-container'); 
        
        if (header && inputContainer && chatBox) {
            const headerHeight = header.offsetHeight;
            const inputHeight = inputContainer.offsetHeight;
            chatBox.style.height = `calc(100vh - ${headerHeight}px - ${inputHeight}px)`;
        }
    }

    // --- LÓGICA PRINCIPAL DO CHAT --- (displayMessage, sendMessage - mantidas como antes, com o blur() já incluído)

    // Exibe uma mensagem na tela (usuário ou Clara)
    function displayMessage(message) {
        if (!chatBox || !message.text) return; 

        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${message.from}`; 

        const contentDiv = document.createElement("div");
        contentDiv.className = "message-content";
        contentDiv.textContent = message.text; 
        contentDiv.style.whiteSpace = 'pre-wrap'; 
        contentDiv.style.wordBreak = 'break-word';
        msgDiv.appendChild(contentDiv);

        const footerDiv = document.createElement("div");
        footerDiv.className = "message-footer";

        const timeSpan = document.createElement("span");
        timeSpan.className = "timestamp";
        timeSpan.textContent = formatTime(); 
        footerDiv.appendChild(timeSpan);

        if (message.from === "me") {
            const checkSpan = document.createElement("span");
            checkSpan.className = "checkmarks";
            checkSpan.innerHTML = '<i class="fas fa-check"></i>'; 
            footerDiv.appendChild(checkSpan);

            const checkmarkSpanForTimeout = checkSpan; 
            setTimeout(() => {
                if (checkmarkSpanForTimeout && chatBox.contains(checkmarkSpanForTimeout)) { 
                    checkmarkSpanForTimeout.innerHTML = '<i class="fas fa-check-double"></i>'; 
                    checkmarkSpanForTimeout.classList.add('read'); 
                }
            }, 1500 + Math.random() * 1000); 
        }
        
        msgDiv.appendChild(footerDiv); 
        chatBox.appendChild(msgDiv); 
        scrollToBottom(); 
    }

    // Função assíncrona para enviar a mensagem
    async function sendMessage(event) {
        if (event) event.preventDefault(); 
        if (!messageInput) return; 

        const messageText = messageInput.value.trim();
        if (messageText === "") return; 

        const currentUserId = getUserId(); 
        
        displayMessage({ from: "me", text: messageText }); 
        if (window.mostrarBotaoInstalacaoSeDisponivel) {
            window.mostrarBotaoInstalacaoSeDisponivel();
          }
          
        
        messageInput.value = "";
        updateSendButton(); 
        messageInput.blur(); // Correção do teclado já está aqui

        setTypingStatus(true); 

        try {
            const response = await fetch("/clara", { 
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ mensagem: messageText, user_id: currentUserId }) 
            });

            if (!response.ok) { 
                let errorDetail = response.statusText; 
                try {
                    const errorData = await response.json();
                    errorDetail = errorData.error || errorData.message || errorDetail;
                } catch (e) { /* Ignora */ }
                throw new Error(`Erro ${response.status}: ${errorDetail}`); 
            }

            const data = await response.json();

            displayMessage({ 
                from: "her", 
                text: data.resposta || "Hmm, não entendi bem o que dizer agora." 
            });

        } catch (error) {
            console.error("Falha na comunicação com a API:", error);
            displayMessage({ 
                from: "her", 
                text: `⚠️ Ops! ${error.message || "Tive um problema para me conectar."}` 
            });
        } finally {
            setTypingStatus(false); 
        }
    }

    // --- <<< ADICIONADO Bloco de Funções para Emoji Picker >>> ---
    // Mostra ou esconde o seletor de emojis
    function toggleEmojiPicker() {
        if (!emojiPicker) {
            console.log("Criando emoji picker...");
            emojiPicker = document.createElement('emoji-picker');
            emojiPicker.style.position = 'absolute'; 
            emojiPicker.style.bottom = '60px'; // Posição inicial (temporária)
            emojiPicker.style.left = '10px';  // Posição inicial (temporária)
            emojiPicker.style.zIndex = '1100'; 
            emojiPicker.classList.add('light'); 

            document.body.appendChild(emojiPicker); 

            emojiPicker.addEventListener('emoji-click', handleEmojiSelection);

             setTimeout(() => {
                document.addEventListener('click', handleClickOutsidePicker, { capture: true, once: true });
             }, 0);

        } else {
            console.log("Fechando emoji picker...");
            closeEmojiPicker();
        }
    }

    // Função auxiliar para fechar/remover o seletor de emojis
    function closeEmojiPicker() {
         if (emojiPicker) {
            emojiPicker.removeEventListener('emoji-click', handleEmojiSelection); 
            if (document.body.contains(emojiPicker)) { 
                 document.body.removeChild(emojiPicker); 
            }
            emojiPicker = null; 
             document.removeEventListener('click', handleClickOutsidePicker, { capture: true }); 
             console.log("Emoji picker fechado.");
         }
    }
    
    // Função chamada quando um emoji é efetivamente clicado no seletor
    function handleEmojiSelection(event) {
        console.log("Emoji selecionado:", event.detail); 
        if (!messageInput) return;

        const emoji = event.detail.unicode; 
        const cursorPos = messageInput.selectionStart; 

        const textBefore = messageInput.value.substring(0, cursorPos);
        const textAfter = messageInput.value.substring(cursorPos);
        messageInput.value = textBefore + emoji + textAfter;

        const newCursorPos = cursorPos + emoji.length;
        messageInput.selectionStart = newCursorPos;
        messageInput.selectionEnd = newCursorPos;

        messageInput.focus(); 
        updateSendButton(); 

        // Opcional: Descomente para fechar após selecionar 1 emoji
        // closeEmojiPicker(); 
    }

    // Função para detectar cliques fora do seletor e fechá-lo
    function handleClickOutsidePicker(event) {
        // Verifica se clicou FORA do picker E FORA do botão de emoji
        if (emojiPicker && !emojiPicker.contains(event.target) && emojiBtn && !emojiBtn.contains(event.target)) {
             console.log("Clique fora detectado, fechando picker.");
            closeEmojiPicker();
        } else if (emojiPicker) {
            // Se clicou dentro ou no botão, o picker pode permanecer aberto. 
            // Adiciona o listener de novo para o *próximo* clique fora.
             document.addEventListener('click', handleClickOutsidePicker, { capture: true, once: true });
        }
    }
    // --- <<< FIM do Bloco de Funções para Emoji Picker >>> ---


    // --- HANDLERS DE EVENTOS ADICIONAIS --- (handleEnterKey, openProfileModal, closeProfileModal - mantidos como antes)

    // Lida com a tecla Enter pressionada no input
    function handleEnterKey(event) {
        if (event.key === "Enter" && !event.shiftKey) { 
            event.preventDefault(); 
            if (messageForm) {
                messageForm.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
            }
        }
    }

    // Abre o modal da foto de perfil
    function openProfileModal() {
        if (modal && modalImg && profilePic) {
            modalImg.src = profilePic.src; 
            modal.style.display = "flex"; 
        }
    }

    // Fecha o modal da foto de perfil
    function closeProfileModal() {
        if (modal) {
            modal.style.display = "none"; 
        }
    }

    // --- INICIALIZAÇÃO DO SCRIPT ---

    // Garante que o DOM esteja carregado antes de executar o init
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init(); // DOM já carregado
    }

})(); // Fim da IIFE