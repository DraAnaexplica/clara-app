// IIFE para encapsular o código e evitar poluir o escopo global
(function() {
    'use strict'; // Habilita modo estrito para pegar erros comuns

    // Cache de elementos DOM frequentemente usados
    let chatBox, messageInput, messageForm, sendBtn, claraStatusElement, 
        profilePic, modal, modalImg, closeModalBtn;

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
        // Considerar remover ou ajustar para mobile se causar problemas com teclado abrindo automaticamente
        messageInput.focus(); 
    }

    // --- FUNÇÕES DE UTILIDADE ---

    // Gera ou recupera um ID de usuário único (localStorage)
    function getUserId() {
        let userId = localStorage.getItem('user_id');
        if (!userId) {
            // Gera um ID mais robusto combinando timestamp e aleatório
            userId = 'user-' + Date.now().toString(36) + Math.random().toString(36).substring(2, 7);
            try {
                localStorage.setItem('user_id', userId);
            } catch (e) {
                console.error("Não foi possível salvar user_id no localStorage:", e);
                // Retorna um ID temporário se localStorage falhar
                return 'user-temp-' + Date.now().toString(36); 
            }
        }
        return userId;
    }

    // Formata a hora atual para HH:MM (formato 24h)
    function formatTime(date = new Date()) {
        // Fallback para caso toLocaleTimeString não funcione como esperado
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
            // Usar 'smooth' pode ter performance variável, 'auto' é mais confiável
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
            // Define a altura do chat para preencher o espaço restante
            chatBox.style.height = `calc(100vh - ${headerHeight}px - ${inputHeight}px)`;
            // Considerar chamar scrollToBottom() aqui somente se a altura MUDOU significativamente
        }
    }

    // --- LÓGICA PRINCIPAL DO CHAT ---

    // Exibe uma mensagem na tela (usuário ou Clara)
    function displayMessage(message) {
        if (!chatBox || !message.text) return; // Não adiciona se não houver chatbox ou texto

        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${message.from}`; // Aplica classe 'me' ou 'her'

        // Cria o elemento para o conteúdo do texto
        const contentDiv = document.createElement("div");
        contentDiv.className = "message-content";
        contentDiv.textContent = message.text; // Usa textContent para segurança
        contentDiv.style.whiteSpace = 'pre-wrap'; // Preserva quebras de linha do texto
        contentDiv.style.wordBreak = 'break-word'; // Quebra palavras longas
        msgDiv.appendChild(contentDiv);

        // Cria o container para o rodapé da mensagem (timestamp e checks)
        const footerDiv = document.createElement("div");
        footerDiv.className = "message-footer";

        // Adiciona o timestamp
        const timeSpan = document.createElement("span");
        timeSpan.className = "timestamp";
        timeSpan.textContent = formatTime(); 
        footerDiv.appendChild(timeSpan);

        // Adiciona os checkmarks SE a mensagem for do usuário ('me')
        if (message.from === "me") {
            const checkSpan = document.createElement("span");
            checkSpan.className = "checkmarks";
            checkSpan.innerHTML = '<i class="fas fa-check"></i>'; // Check inicial (enviado)
            footerDiv.appendChild(checkSpan);

            // Simula a atualização para "lido" (check duplo azul)
            // Em um app real, isso seria acionado por um evento do backend/outro usuário
            const checkmarkSpanForTimeout = checkSpan; 
            setTimeout(() => {
                // Verifica se o elemento ainda existe no DOM antes de modificar
                if (checkmarkSpanForTimeout && chatBox.contains(checkmarkSpanForTimeout)) { 
                    checkmarkSpanForTimeout.innerHTML = '<i class="fas fa-check-double"></i>'; 
                    checkmarkSpanForTimeout.classList.add('read'); 
                }
            }, 1500 + Math.random() * 1000); // Tempo de simulação um pouco variável
        }
        
        msgDiv.appendChild(footerDiv); // Adiciona o rodapé completo à mensagem
        chatBox.appendChild(msgDiv); // Adiciona a mensagem ao chat
        scrollToBottom(); // Garante que a nova mensagem seja visível
    }

    // Função assíncrona para enviar a mensagem
    async function sendMessage(event) {
        if (event) event.preventDefault(); // Impede o envio padrão do formulário
        if (!messageInput) return; // Sai se o input não existir

        const messageText = messageInput.value.trim();
        if (messageText === "") return; // Não faz nada se a mensagem estiver vazia

        const currentUserId = getUserId(); // Pega o ID do usuário
        
        // Mostra a mensagem do usuário na tela imediatamente
        displayMessage({ from: "me", text: messageText }); 
        
        // Limpa o campo de input, atualiza o botão e tira o foco (esconde teclado mobile)
        messageInput.value = "";
        updateSendButton(); 
        messageInput.blur(); // <--- CORREÇÃO DO TECLADO

        setTypingStatus(true); // Mostra "digitando..."

        try {
            // Faz a requisição para o backend
            const response = await fetch("/clara", { // Endpoint relativo (ajuste se necessário)
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    // Adicionar outros headers se necessário (ex: autenticação)
                },
                // Body no formato esperado pelo backend original
                body: JSON.stringify({ mensagem: messageText, user_id: currentUserId }) 
            });

            // Verifica se a resposta da requisição foi bem-sucedida
            if (!response.ok) { 
                let errorDetail = response.statusText; // Detalhe padrão do erro HTTP
                // Tenta obter uma mensagem de erro mais específica do corpo da resposta JSON
                try {
                    const errorData = await response.json();
                    errorDetail = errorData.error || errorData.message || errorDetail;
                } catch (e) { /* Falha ao ler corpo do erro, usa o statusText */ }
                // Lança um erro para ser pego pelo bloco catch
                throw new Error(`Erro ${response.status}: ${errorDetail}`); 
            }

            // Converte a resposta bem-sucedida para JSON
            const data = await response.json();

            // Simula um delay na resposta para parecer mais natural (opcional)
            // await new Promise(resolve => setTimeout(resolve, 300 + Math.random() * 400)); 

            // Exibe a resposta da Clara
            // Usa a chave 'resposta' do JSON retornado pelo backend original
            displayMessage({ 
                from: "her", 
                text: data.resposta || "Hmm, não entendi bem o que dizer agora." // Fallback
            });

        } catch (error) {
            // Captura erros da rede ou erros lançados (response.ok === false)
            console.error("Falha na comunicação com a API:", error);
            // Mostra uma mensagem de erro amigável no chat
            displayMessage({ 
                from: "her", 
                text: `⚠️ Ops! ${error.message || "Tive um problema para me conectar."}` 
            });
        } finally {
            // Este bloco SEMPRE executa, com sucesso ou erro
            setTypingStatus(false); // Garante que "digitando..." seja desativado
        }
    }

    // --- HANDLERS DE EVENTOS ADICIONAIS ---

    // Lida com a tecla Enter pressionada no input
    function handleEnterKey(event) {
        // Verifica se foi Enter E se Shift NÃO estava pressionado (permite Shift+Enter para nova linha)
        if (event.key === "Enter" && !event.shiftKey) { 
            event.preventDefault(); // Impede o comportamento padrão do Enter (nova linha, etc.)
            
            // Dispara o evento de 'submit' no formulário, acionando a função sendMessage
            if (messageForm) {
                // Usar requestSubmit() é mais moderno, mas dispatchEvent é mais compatível
                messageForm.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
            }
        }
    }

    // Abre o modal da foto de perfil
    function openProfileModal() {
        if (modal && modalImg && profilePic) {
            modalImg.src = profilePic.src; 
            modal.style.display = "flex"; // Usa 'flex' para habilitar centralização via CSS
            // Adicionar Acessibilidade: Travar foco no modal aqui seria ideal
        }
    }

    // Fecha o modal da foto de perfil
    function closeProfileModal() {
        if (modal) {
            modal.style.display = "none"; 
             // Adicionar Acessibilidade: Retornar foco para o elemento que abriu o modal
        }
    }

    // --- INICIALIZAÇÃO DO SCRIPT ---

    // Garante que o DOM esteja carregado antes de executar o init
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        // DOM já carregado, executa imediatamente
        init();
    }

})(); // Fim da IIFE (Immediately Invoked Function Expression)

