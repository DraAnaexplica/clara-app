// IIFE para encapsular o código e evitar poluir o escopo global
(function() {
    'use strict'; // Habilita modo estrito para pegar erros comuns

    // Cache de elementos DOM frequentemente usados
    let chatBox, messageInput, messageForm, sendBtn, claraStatusElement, profilePic, modal, modalImg, closeModalBtn;

    // Função para inicializar tudo quando o DOM estiver pronto
    function init() {
        // Seleciona os elementos uma vez
        chatBox = document.getElementById("chat-box");
        messageInput = document.getElementById("mensagem");
        messageForm = document.getElementById("mensagem-form");
        sendBtn = document.querySelector('.send-btn');
        claraStatusElement = document.getElementById("clara-status");
        profilePic = document.getElementById("profile-pic");
        modal = document.getElementById("modal");
        modalImg = document.getElementById("modal-img");
        closeModalBtn = document.querySelector(".modal .close"); // Seleciona o botão de fechar dentro do modal

        // Verifica se os elementos essenciais existem antes de adicionar listeners
        if (messageForm && messageInput && sendBtn) {
            messageForm.addEventListener("submit", sendMessage);
            messageInput.addEventListener("input", updateSendButton);
            messageInput.addEventListener("keypress", handleEnterKey);
            updateSendButton(); // Define o estado inicial do botão (microfone)
        } else {
            console.error("Elementos essenciais do formulário não encontrados!");
            return; // Interrompe a inicialização se algo faltar
        }

        if (profilePic && modal && modalImg && closeModalBtn) {
             profilePic.addEventListener("click", openProfileModal);
             closeModalBtn.addEventListener("click", closeProfileModal);
             modal.addEventListener("click", function(event) {
                // Fecha modal se clicar fora da imagem
                if (event.target === modal) {
                    closeProfileModal();
                }
             });
        }
        
        // Ajustes de layout (mantidos do JS original)
        // Removido handleKeyboard com visualViewport pois pode ser complexo e buggy,
        // confiar no CSS e comportamento padrão pode ser melhor inicialmente.
        // Se o teclado cobrir o input, considerar reavaliar.
        window.addEventListener('resize', adjustChatHeight);
        adjustChatHeight(); // Ajusta altura inicial

        // Foco inicial no input
        messageInput.focus();

        // Exemplo: Enviar uma mensagem inicial de "Clara" se necessário
        // displayMessage({ from: "her", text: "Olá! Como posso ajudar?" });
    }

    // Gera ou recupera o user_id do localStorage (mantido)
    function getUserId() {
        let userId = localStorage.getItem('user_id');
        if (!userId) {
            userId = 'user-' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5); // ID um pouco mais robusto
            localStorage.setItem('user_id', userId);
        }
        return userId;
    }

    // Formata a hora (mantido)
    function formatTime(date = new Date()) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false }); // formato 24h
    }

    // Exibe mensagens (Refatorado para usar textContent e criar DOM)
    function displayMessage(message) {
        if (!chatBox) return; // Verifica se chatBox existe

        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${message.from}`; // 'me' ou 'her'

        // Conteúdo da mensagem (Seguro com textContent)
        const contentDiv = document.createElement("div");
        contentDiv.className = "message-content";
        // Usa textContent para inserir o texto da mensagem com segurança
        contentDiv.textContent = message.text; 
        // Permite quebras de linha no texto (ex: \n) sejam exibidas
        contentDiv.style.whiteSpace = 'pre-wrap'; 
        contentDiv.style.wordBreak = 'break-word';
        msgDiv.appendChild(contentDiv);

        // Container para timestamp e checks
        const footerDiv = document.createElement("div");
        footerDiv.className = "message-footer";

        // Timestamp
        const timeSpan = document.createElement("span");
        timeSpan.className = "timestamp";
        timeSpan.textContent = formatTime(); 
        footerDiv.appendChild(timeSpan);

        // Checkmarks (Só para mensagens 'me')
        if (message.from === "me") {
            const checkSpan = document.createElement("span");
            checkSpan.className = "checkmarks";
            // Ícone inicial (pode ser um ou dois checks cinzas via CSS ou um aqui)
            checkSpan.innerHTML = '<i class="fas fa-check"></i>'; 
            footerDiv.appendChild(checkSpan);

            // Simula mudança para lido (check duplo azul) após um tempo
             // Guardar referência ao span de check para o timeout
            const checkmarkSpanForTimeout = checkSpan; 
            setTimeout(() => {
                if (checkmarkSpanForTimeout) { // Verifica se ainda existe
                    checkmarkSpanForTimeout.innerHTML = '<i class="fas fa-check-double"></i>'; 
                    checkmarkSpanForTimeout.classList.add('read'); 
                }
            }, 1500); // Tempo da simulação (ajuste se quiser)
        }
        
        msgDiv.appendChild(footerDiv); // Adiciona o rodapé (timestamp/checks)
        chatBox.appendChild(msgDiv);
        scrollToBottom(); // Rola para o final
    }

    // Rola para o final do chat (mantido)
    function scrollToBottom() {
        if (chatBox) {
            // Usar 'smooth' pode ser bom, mas 'auto' é mais garantido
            chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: 'auto' }); 
        }
    }

    // Envia mensagem (Refatorado com async/await, typing indicator)
    async function sendMessage(event) {
        if (event) event.preventDefault(); // Previne recarregamento da página
        
        if (!messageInput) return; // Verifica se input existe

        const message = messageInput.value.trim();
        if (message === "") return; // Não envia mensagem vazia
        
        const userId = getUserId(); // Pega o user ID
        
        // Exibe a mensagem do usuário imediatamente
        displayMessage({ from: "me", text: message }); 
        
        // Limpa o input e atualiza o botão
        messageInput.value = "";
        updateSendButton(); 
        // messageInput.focus(); // Re-focar pode ser irritante em mobile, opcional

        setTypingStatus(true); // LIGA o "digitando..."

        try {
            // Usa o endpoint relativo (melhor para Flask)
            const response = await fetch("/clara", { 
                method: "POST",
                headers: { "Content-Type": "application/json" },
                // Usa a estrutura de body esperada pelo seu backend original
                body: JSON.stringify({ mensagem: message, user_id: userId }) 
            });

            // Verifica se a resposta HTTP foi bem-sucedida (status 2xx)
            if (!response.ok) { 
                // Tenta pegar mais detalhes do erro se o backend enviar
                let errorMsg = `Erro HTTP: ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorMsg = errorData.error || errorMsg; // Usa msg de erro do backend se disponível
                } catch (e) { /* Ignora erro ao parsear corpo do erro */ }
                throw new Error(errorMsg);
            }

            const data = await response.json();

            // Simular um pequeno delay da resposta (opcional)
            // await new Promise(resolve => setTimeout(resolve, Math.random() * 500 + 200)); 

            // Exibe a resposta de "Clara"
            displayMessage({ 
                from: "her", 
                // Usa a chave de resposta esperada pelo JS original
                text: data.resposta || "Não recebi uma resposta válida." 
            });

        } catch (error) {
            console.error("Erro ao enviar/receber mensagem:", error);
            // Exibe uma mensagem de erro no chat
            displayMessage({ 
                from: "her", 
                text: `⚠️ ${error.message || "Ocorreu um erro na comunicação."}` 
            });
        } finally {
            // Garante que o status "digitando" seja desativado, mesmo se houver erro
            setTypingStatus(false); // DESLIGA o "digitando..."
        }
    }

    // Atualiza o botão enviar/microfone (mantido, ajustado para pegar sendBtn cacheado)
    function updateSendButton() {
        if (!sendBtn || !messageInput) return; // Verifica se existem

        if (messageInput.value.trim().length > 0) {
            // Muda para ícone de enviar (avião de papel)
            sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
            // sendBtn.style.backgroundColor = 'var(--button-send-bg)'; // Cor já definida no CSS
        } else {
            // Muda para ícone de microfone
            sendBtn.innerHTML = '<i class="fas fa-microphone"></i>';
            // sendBtn.style.backgroundColor = 'var(--button-send-bg)'; // Cor já definida no CSS
        }
    }

    // Atualiza o status da Clara no topo (nova função)
    function setTypingStatus(isTyping) {
        if (claraStatusElement) { // Verifica se o elemento existe
            // Adiciona/remove uma classe para estilização opcional via CSS
            claraStatusElement.classList.toggle('typing', isTyping); 
            // Define o texto
            claraStatusElement.textContent = isTyping ? "digitando..." : "online"; 
        }
    }

    // Função para lidar com a tecla Enter (nova função)
    function handleEnterKey(event) {
        // Verifica se foi Enter E se o Shift NÃO estava pressionado
        if (event.key === "Enter" && !event.shiftKey) { 
            event.preventDefault(); // Impede o comportamento padrão (nova linha, submit padrão)
            
            // Dispara o evento de submit do formulário para chamar nossa função `sendMessage`
            if (messageForm) {
                // Cria e dispara um evento de submit que pode ser cancelado
                const submitEvent = new Event('submit', { cancelable: true, bubbles: true });
                messageForm.dispatchEvent(submitEvent);
            }
        }
    }

    // Ajusta a altura da área de chat (mantido, ajustado para pegar elementos cacheados)
    function adjustChatHeight() {
        const header = document.querySelector('header'); // Pode cachear se não mudar
        const inputContainer = document.querySelector('.input-container'); // Pode cachear
        
        if (header && inputContainer && chatBox) {
            const headerHeight = header.offsetHeight;
            const inputHeight = inputContainer.offsetHeight;
            // Calcula altura restante
            chatBox.style.height = `calc(100vh - ${headerHeight}px - ${inputHeight}px)`;
            // scrollToBottom(); // Rolar aqui pode ser excessivo em cada resize
        }
    }

    // Funções do Modal (mantidas, ajustadas para pegar elementos cacheados)
    function openProfileModal() {
        if (modal && modalImg && profilePic) {
            modalImg.src = profilePic.src; // Define a imagem do modal
            modal.style.display = "flex"; // Usa flex para centralizar (definido no CSS)
        }
    }

    function closeProfileModal() {
        if (modal) {
            modal.style.display = "none"; // Oculta o modal
        }
    }

    // Event listener para carregar o DOM e iniciar o script
    document.addEventListener("DOMContentLoaded", init);

})(); // Fim da IIFE

