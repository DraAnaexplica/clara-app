// Executa o código apenas quando o DOM estiver completamente carregado
document.addEventListener('DOMContentLoaded', () => {

    // Seletores Globais (melhora performance não buscando toda hora)
    const chatBox = document.getElementById("chat-box");
    const messageForm = document.getElementById("mensagem-form");
    const messageInput = document.getElementById("mensagem"); // Agora é textarea
    const sendBtn = document.querySelector('.send-btn');
    const statusElement = document.querySelector('.status'); // Elemento de status no header

    // Verifica se elementos essenciais existem
    if (!chatBox || !messageForm || !messageInput || !sendBtn || !statusElement) {
        console.error("Erro Crítico: Elementos essenciais do chat não encontrados no DOM.");
        // Poderia exibir uma mensagem de erro para o usuário aqui
        return; // Interrompe a execução se algo estiver faltando
    }

    // --- Gerenciamento do User ID ---
    function getUserId() {
        const storageKey = 'clara_user_id'; // Usar prefixo específico
        let userId = localStorage.getItem(storageKey); 
        if (!userId) {
            // Gera um ID mais robusto (pseudo-UUID)
            userId = 'user-' + Date.now().toString(36) + Math.random().toString(36).substring(2, 15);
            try {
                localStorage.setItem(storageKey, userId);
                console.log("Novo User ID gerado e salvo:", userId);
            } catch (e) {
                console.error("Erro ao salvar User ID no localStorage:", e);
                // App ainda pode funcionar, mas sem histórico persistente entre sessões
                // Poderia usar um ID temporário apenas para esta sessão
            }
        }
        return userId;
    }

    // --- Funções de Exibição ---

    // Formata a hora atual ou de uma data específica
    function formatTime(date = new Date()) {
        return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    }

    // Adiciona uma mensagem à caixa de chat
    function displayMessage(message, isUserMessage = false) {
        if (!message || typeof message.text !== 'string') {
            console.error("displayMessage: Dados da mensagem inválidos.", message);
            return;
        }
        
        const msgDiv = document.createElement("div");
        const senderClass = message.from === 'me' ? 'me' : 'her';
        msgDiv.className = `message ${senderClass}`; 
        
        // Sanitiza a mensagem antes de inserir como HTML (prevenção básica contra XSS)
        // Cria um nó de texto para evitar interpretação de HTML na mensagem
        const messageTextNode = document.createTextNode(message.text);
        const messageContentDiv = document.createElement('div');
        messageContentDiv.className = 'message-content';
        messageContentDiv.appendChild(messageTextNode); // Adiciona como texto puro
        
        // Converte \n em <br> APÓS sanitizar (ou use CSS white-space: pre-wrap)
        messageContentDiv.innerHTML = messageContentDiv.innerHTML.replace(/\n/g, '<br>');

        // Cria o span do timestamp
        const timestampSpan = document.createElement('span');
        timestampSpan.className = 'timestamp';
        timestampSpan.textContent = message.timestamp || formatTime(); // Usa timestamp da mensagem se existir, senão o atual

        // Monta a div da mensagem
        msgDiv.appendChild(messageContentDiv);
        msgDiv.appendChild(timestampSpan);

        // Adiciona a div da mensagem ao chatBox
        chatBox.appendChild(msgDiv);
        
        // Rola para o final para mostrar a nova mensagem
        scrollToBottom();
    }

    // Rola a caixa de chat para a mensagem mais recente
    function scrollToBottom() {
        // Usamos requestAnimationFrame para melhor performance de scroll
        requestAnimationFrame(() => {
            chatBox.scrollTop = chatBox.scrollHeight;
        });
    }

    // Mostra indicador de "digitando..." no header
    function showTypingIndicator() {
         statusElement.textContent = 'digitando...';
         statusElement.classList.add('typing');
    }

    // Remove a mensagem de carregamento ("digitando...")
    function hideTypingIndicator() {
        statusElement.textContent = 'online'; // Volta para online
        statusElement.classList.remove('typing');
    }


    // --- Lógica de Envio de Mensagem ---

    let isSending = false; // Flag para evitar envios múltiplos

    async function handleFormSubmit(event) {
        if (event) event.preventDefault(); // Previne recarregamento da página
        
        if (isSending) {
             console.warn("Envio já está em progresso.");
             return; // Evita envio duplicado
        }

        const messageText = messageInput.value.trim();
        if (messageText === "") {
            console.log("Tentativa de enviar mensagem vazia.");
            return; // Não envia mensagem vazia
        }
        
        const userId = getUserId();
        if (!userId) {
             console.error("User ID não encontrado. Não é possível enviar mensagem.");
             displayMessage({ from: "her", text: "⚠️ Erro: Não consegui identificar você. Recarregue a página." });
             return;
        }

        const timestamp = formatTime(); // Pega a hora atual para exibição imediata
        
        // --- Início do Processo de Envio ---
        isSending = true;
        sendBtn.disabled = true; // Desabilita botão durante envio

        // 1. Exibe a mensagem do usuário imediatamente
        displayMessage({ 
            from: "me", 
            text: messageText,
            timestamp: timestamp
        }, true); 
        
        // 2. Limpa o input e atualiza o botão/altura
        messageInput.value = "";
        updateSendButtonState();
        adjustTextareaHeight();
        // messageInput.focus(); // Re-foca no input após enviar

        // 3. Mostra indicador de "digitando..."
        showTypingIndicator();

        // 4. Envia a mensagem para o backend
        try {
            const response = await fetch("/chat", { // Endpoint definido em app.py
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    "Accept": "application/json" // Indica que esperamos JSON de volta
                },
                body: JSON.stringify({ mensagem: messageText, user_id: userId })
            });

            // Processa a resposta (erro ou sucesso)
            await processServerResponse(response);

        } catch (error) {
            console.error("Erro de rede ao enviar mensagem:", error);
            let networkErrorMsg = "⚠️ Ocorreu um erro de conexão. Verifique sua internet e tente novamente.";
            if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
                 // Erro específico de rede
                 console.error("Falha no fetch, possível problema de rede ou CORS.");
            } else {
                 networkErrorMsg = `⚠️ Erro inesperado na comunicação: ${error.message}`; // Outro tipo de erro
            }
            displayMessage({ from: "her", text: networkErrorMsg });
        } finally {
            // --- Fim do Processo de Envio ---
            hideTypingIndicator(); // Garante que esconde "digitando"
            isSending = false; // Libera para novo envio
            sendBtn.disabled = false; // Reabilita o botão
            messageInput.focus(); // Foca no input para próxima mensagem
        }
    }

    // Processa a resposta recebida do servidor
    async function processServerResponse(response) {
         if (!response.ok) {
             // Tenta ler o erro do corpo JSON se disponível
             let errorMsg = `Erro ${response.status}: ${response.statusText}`;
             try {
                 const errorData = await response.json();
                 if (errorData && errorData.error) {
                     errorMsg = `⚠️ ${errorData.error}`;
                 } else {
                     // Se não houver JSON de erro, mostra o texto da resposta (se houver)
                     const errorText = await response.text();
                     if (errorText) {
                         errorMsg = `⚠️ Erro ${response.status}: ${errorText.substring(0, 100)}`; // Limita tamanho
                     }
                 }
             } catch (e) {
                 console.warn("Não foi possível decodificar JSON/Texto do erro:", e);
             }
              console.error("Erro na resposta do servidor:", errorMsg);
              displayMessage({ from: "her", text: errorMsg });
              return; 
         }
 
         // Processa a resposta JSON bem-sucedida
         try {
             const data = await response.json();
             if (data && typeof data.resposta === 'string') {
                  displayMessage({ from: "her", text: data.resposta });
             } else {
                  console.error("Resposta JSON do servidor em formato inválido:", data);
                  displayMessage({ from: "her", text: "⚠️ Recebi uma resposta inesperada do servidor." });
             }
         } catch (jsonError) {
              console.error("Erro ao decodificar JSON da resposta bem-sucedida:", jsonError);
              displayMessage({ from: "her", text: "⚠️ Tive problemas para ler a resposta do servidor." });
         }
    }


    // --- Atualizações da Interface ---

    // Atualiza o estado (ícone e label) do botão de enviar
    function updateSendButtonState() {
        const hasText = messageInput.value.trim().length > 0;
        
        if (hasText) {
            sendBtn.classList.add('has-text');
            sendBtn.setAttribute('aria-label', 'Enviar mensagem');
            sendBtn.setAttribute('title', 'Enviar mensagem');
            // Troca ícone via CSS (ver style.css)
        } else {
            sendBtn.classList.remove('has-text');
            sendBtn.setAttribute('aria-label', 'Gravar áudio');
            sendBtn.setAttribute('title', 'Gravar áudio');
            // Troca ícone via CSS (ver style.css)
        }
        // A mudança real do ícone é feita no CSS baseado na classe 'has-text'
    }

    // Ajusta a altura do textarea conforme o conteúdo (auto-grow)
    function adjustTextareaHeight() {
        // Necessário para calcular scrollHeight corretamente
        messageInput.style.height = 'auto'; 
        
        const maxHeight = 105; // Valor max-height definido no CSS
        const scrollHeight = messageInput.scrollHeight;
        
        // Define a altura baseada no scrollHeight, limitado pela maxHeight
        messageInput.style.height = `${Math.min(scrollHeight, maxHeight)}px`;

        // Habilita/desabilita scroll vertical se necessário
        messageInput.style.overflowY = scrollHeight > maxHeight ? 'auto' : 'hidden';
    }

    // --- Gerenciamento de Teclado e Viewport ---

    // Listener simples para rolar ao fim em mudanças de viewport
    function handleViewportChange() {
        // Apenas rola para o fim; ajustes complexos de layout são frágeis
        scrollToBottom(); 
    }


    // --- Inicialização ---
    function initChat() {
        console.log("Iniciando interface do chat...");
        
        // Adiciona listeners de evento
        messageForm.addEventListener("submit", handleFormSubmit);
        
        messageInput.addEventListener("input", () => {
            updateSendButtonState();
            adjustTextareaHeight();
        });
        
        // Permite enviar com Enter (Shift+Enter para nova linha)
        messageInput.addEventListener("keydown", (e) => {
            if (e.key === 'Enter' && !e.shiftKey && !isSending) { // Só envia se não estiver enviando
                e.preventDefault(); // Impede nova linha no textarea
                handleFormSubmit(); // Chama a função de envio
            }
        });

        // Atualiza estado inicial do botão e altura do textarea
        updateSendButtonState();
        adjustTextareaHeight();

        // Listener para mudanças no viewport (teclado, rotação, redimensionamento)
        if (window.visualViewport) {
            window.visualViewport.addEventListener('resize', handleViewportChange);
            // window.visualViewport.addEventListener('scroll', handleViewportChange); // Scroll pode ser demais
        } else {
            window.addEventListener('resize', handleViewportChange);
        }
        
        // Foco inicial no input (bom para desktop)
        // setTimeout(() => messageInput.focus(), 100); // Pequeno delay

        // Carregar histórico inicial (se implementado no backend)
        // loadInitialHistory(); 

        console.log("Interface do chat inicializada. User ID:", getUserId());
        
        // Exibe uma mensagem inicial de boas-vindas (opcional)
        // displayMessage({from: "her", text: "Olá! Como posso ajudar?"});
    }
    
    // --- Opcional: Carregar Histórico Inicial ---
    async function loadInitialHistory() {
         const userId = getUserId();
         if (!userId) return;

         console.log("Tentando carregar histórico inicial...");
         try {
             // Assumindo um endpoint GET /history?user_id=... que retorna [{from: '...', text: '...', timestamp: '...'}, ...]
             const response = await fetch(`/history?user_id=${userId}`); 
             if (response.ok) {
                 const history = await response.json();
                 if (Array.isArray(history)) {
                     chatBox.innerHTML = ''; // Limpa chatbox antes de carregar histórico
                     history.forEach(msg => displayMessage(msg)); 
                     console.log(`Histórico carregado: ${history.length} mensagens.`);
                     scrollToBottom(); // Rola para o fim após carregar
                 } else {
                     console.warn("Formato inválido recebido para histórico.");
                 }
             } else {
                 console.warn(`Não foi possível carregar histórico: ${response.status} ${response.statusText}`);
             }
         } catch (error) {
             console.error("Erro de rede ao carregar histórico:", error);
         }
    }

    // --- Execução da Inicialização ---
    initChat();

}); // Fim do DOMContentLoaded listener