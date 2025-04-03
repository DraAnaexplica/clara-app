// ARQUIVO JAVASCRIPT FINAL (script_final.js)
// Base do MELHORADO com funcionalidades do ATUAL integradas

// Elementos do DOM (Seletores do HTML Final)
const chatBox = document.getElementById("chat-box");
const messageInput = document.getElementById("mensagem"); // ID do input do ATUAL
const sendButton = document.getElementById("send-btn");  // ID do botão de enviar
const claraStatusElement = document.getElementById("clara-status"); // Status no header
const form = document.getElementById("mensagem-form"); // Formulário do input
const modal = document.getElementById("modal");
const modalImg = document.getElementById("modal-img");
const profilePic = document.getElementById("profile-pic");
const closeBtn = modal ? modal.querySelector(".close") : null; // Botão fechar dentro do modal

let originalStatusText = "online"; // Guarda o status original

// --- Funções do ATUAL (Adaptadas) ---

// Gera ou recupera o user_id do localStorage
function getUserId() {
    let userId = localStorage.getItem('user_id');
    if (!userId) {
        userId = 'user-' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
        localStorage.setItem('user_id', userId);
    }
    return userId;
}

// Função para formatar a hora
function formatTime(date = new Date()) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Função para rolar para o final do chat
function scrollToBottom() {
    if (chatBox) {
        chatBox.scrollTop = chatBox.scrollHeight;
    }
}

// Atualiza o botão de enviar/microfone (Lógica do ATUAL)
function updateSendButtonIcon() {
    if (!sendButton || !messageInput) return;
    const hasText = messageInput.value.trim().length > 0;
    // Muda o ícone dentro do botão
    sendButton.innerHTML = hasText
        ? '<i class="fas fa-paper-plane"></i>' // Ícone de enviar
        : '<i class="fas fa-microphone"></i>'; // Ícone de microfone
    // O CSS já cuida da cor de fundo baseado na classe/ID ou ícone
}

// --- Funções do MELHORADO (Adaptadas) ---

// Adiciona mensagem ao chat (COMBINAÇÃO: usa classes do MELHORADO, estrutura do ATUAL)
function addMessage(sender, text, time, status) {
    if (!chatBox) return;

    const msgDiv = document.createElement("div");
    // Usa classes 'user' ou 'clara' (do MELHORADO)
    msgDiv.classList.add("message", sender);

    // Cria estrutura interna (baseada no ATUAL)
    const contentDiv = document.createElement("div");
    contentDiv.classList.add("message-content");
    contentDiv.textContent = text; // Usar textContent para segurança

    const metaDiv = document.createElement("div");
    metaDiv.classList.add("message-meta");

    const timeSpan = document.createElement("span");
    timeSpan.classList.add("timestamp");
    timeSpan.textContent = time || formatTime();
    metaDiv.appendChild(timeSpan);

    // Adiciona checkmarks apenas para mensagens 'user' (usuário)
    if (sender === "user") {
        const checkmarksSpan = document.createElement("span");
        checkmarksSpan.classList.add("checkmarks");
        checkmarksSpan.innerHTML = '<i class="fas fa-check"></i>'; // Padrão: enviado

        // Atualiza checkmarks com base no status (se fornecido)
        if (status === 'read') {
             checkmarksSpan.classList.add('read');
             checkmarksSpan.innerHTML = '<i class="fas fa-check-double"></i>';
        } else if (status === 'delivered') {
             // Poderia ter estilo diferente (ex: duplo check cinza)
             checkmarksSpan.innerHTML = '<i class="fas fa-check-double"></i>';
        }
        metaDiv.appendChild(checkmarksSpan);
    }

    msgDiv.appendChild(contentDiv);
    msgDiv.appendChild(metaDiv);
    chatBox.appendChild(msgDiv);
    scrollToBottom();

    // Simulação de Leitura (Opcional - pode ser removido ou substituído)
    // if (sender === "user" && status !== 'read') {
    //     setTimeout(() => {
    //         const checks = msgDiv.querySelector('.checkmarks');
    //         if (checks) {
    //             checks.classList.add('read');
    //             checks.innerHTML = '<i class="fas fa-check-double"></i>';
    //         }
    //     }, 2500); // Simula leitura após 2.5s
    // }
}

// Atualiza o status da Clara no topo (do MELHORADO)
function setTypingStatus(isTyping) {
    if (claraStatusElement) {
        if (isTyping) {
            if (claraStatusElement.textContent !== "digitando...") {
                originalStatusText = claraStatusElement.textContent;
            }
            claraStatusElement.textContent = "digitando...";
        } else {
            claraStatusElement.textContent = originalStatusText;
        }
    }
}

// Envia mensagem (COMBINAÇÃO: async/await do MELHORADO, payload/ID do ATUAL)
async function handleSendMessage(event) {
    if(event) event.preventDefault(); // Previne submit padrão do form
    if (!messageInput) return;

    const messageText = messageInput.value.trim();
    if (messageText === "") return;

    const userId = getUserId(); // Pega ID (do ATUAL)
    const messageToSend = messageText; // Guarda antes de limpar

    // 1. Exibe a mensagem do usuário
    addMessage("user", messageToSend, null, 'sent'); // Usa 'user', status 'sent'

    messageInput.value = ""; // Limpa input
    updateSendButtonIcon(); // Atualiza ícone do botão
    // messageInput.focus(); // Foco opcional

    // 2. Mostra "digitando..."
    setTypingStatus(true);

    try {
        // 3. Envia para o backend
        // USA O ENDPOINT E PAYLOAD DO *SEU* BACKEND ATUAL (`/clara`, `mensagem`, `user_id`)
        // SE o backend mudou para o do MELHORADO, ajuste o endpoint e o `body` abaixo
        const response = await fetch("/clara", { // Endpoint do ATUAL
            method: "POST",
            headers: { "Content-Type": "application/json" },
            // Payload do ATUAL (mensagem, user_id)
            body: JSON.stringify({ mensagem: messageToSend, user_id: userId })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        // 4. Simula tempo de resposta e exibe resposta da Clara
        setTimeout(() => {
            setTypingStatus(false);
            // Usa 'clara' como sender, pega 'resposta' do JSON (do ATUAL)
            addMessage("clara", data.resposta || "Desculpe, não consegui processar agora.");
        }, 800 + Math.random() * 700); // Delay variado

    } catch (error) {
        console.error("Erro ao enviar/receber mensagem:", error);
        setTypingStatus(false);
        addMessage("clara", "⚠️ Ops! Tive um problema de conexão. Tente de novo.");
    }
}

// --- INICIALIZAÇÃO E EVENT LISTENERS ---

function initializeChat() {
    // Guarda status inicial do header
    if (claraStatusElement) {
        originalStatusText = claraStatusElement.textContent;
    }

    // Listener para envio pelo formulário (botão submit)
    if (form) {
        form.addEventListener("submit", handleSendMessage);
    }

    // Listener para atualizar botão ao digitar
    if (messageInput) {
        messageInput.addEventListener("input", updateSendButtonIcon);

        // Listener para enviar com Enter (do MELHORADO)
        messageInput.addEventListener("keypress", function (e) {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage(); // Chama a função de envio
            }
        });
    }

    // Define estado inicial do botão
    updateSendButtonIcon();

    // Listeners do Modal (do ATUAL)
    if (profilePic && modal && modalImg && closeBtn) {
        profilePic.onclick = function() {
          modal.style.display = "flex"; // Usa flex para centralizar
          // Adiciona classe 'active' para animações CSS
          setTimeout(() => modal.classList.add('active'), 10);
          modalImg.src = this.src;
          modalImg.alt = this.alt;
        }

        const closeModal = () => {
            modal.classList.remove('active');
            // Espera a animação de fade-out terminar antes de esconder
            setTimeout(() => modal.style.display = "none", 300); // 300ms = duração da transição CSS
        }

        closeBtn.onclick = closeModal;

        // Fechar ao clicar fora
        modal.onclick = function(event) {
            if (event.target === modal) {
                 closeModal();
            }
        }
    } else {
        console.warn("Elementos do modal não encontrados.");
    }

    // Rola para baixo ao iniciar (caso haja histórico)
    scrollToBottom();

     // Adiciona uma mensagem inicial da Clara (Exemplo)
     addMessage("clara", "Oi! 😊 Como posso te ajudar hoje?");
}

// Executa a inicialização quando o DOM estiver pronto
document.addEventListener("DOMContentLoaded", initializeChat);
