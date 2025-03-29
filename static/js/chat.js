// Gera ou recupera o user_id do localStorage
function getUserId() {
    let userId = localStorage.getItem('user_id');
    if (!userId) {
        userId = 'user-' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('user_id', userId);
    }
    return userId;
}

// Função para formatar a hora
function formatTime(date = new Date()) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Função pra exibir mensagens
function displayMessage(message) {
    const chatBox = document.getElementById("chat-box");
    const msgDiv = document.createElement("div");
    
    msgDiv.className = `message ${message.from}`;
    msgDiv.innerHTML = `
        <div class="message-content">${message.text}</div>
        <span class="timestamp">${formatTime()}</span>
        ${message.from === "me" ? '<span class="checkmarks"><i class="fas fa-check-double"></i></span>' : ''}  `;
    
    chatBox.appendChild(msgDiv);
    scrollToBottom();
    
    // Simula a confirmação de leitura após 2 segundos
    if (message.from === "me") {
        setTimeout(() => {
            const checkmarks = msgDiv.querySelector('.checkmarks');
            if (checkmarks) {
                checkmarks.innerHTML = '<i class="fas fa-check-double"></i><i class="fas fa-check-double"></i>';  checkmarks.classList.add('read');
            }
        }, 2000); // 2 segundos de delay
    }
}

// Função para rolar para o final do chat
function scrollToBottom() {
    const chatBox = document.getElementById("chat-box");
    chatBox.scrollTop = chatBox.scrollHeight;  // Removido o setTimeout (mais eficiente)
}

// Função pra enviar mensagem
function sendMessage(event) {
    event.preventDefault();
    
    const messageInput = document.getElementById("mensagem");
    const message = messageInput.value.trim();
    if (message === "") return;
    
    displayMessage({ 
        from: "me", 
        text: message 
    });
    
    messageInput.value = "";
    updateSendButton();
    messageInput.focus();  // Mantém o foco no input após enviar
    
    const userId = getUserId();
    
    fetch("/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mensagem: message, user_id: userId })
    })
    .then(response => response.json())
    .then(data => {
        displayMessage({ 
            from: "her", 
            text: data.resposta 
        });
    })
    .catch(error => {
        console.error("Erro ao receber resposta:", error);  // Mensagem de erro mais específica
        displayMessage({ 
            from: "her", 
            text: "⚠️ Ocorreu um erro ao receber a resposta. Por favor, tente novamente."
        });
    });
}

// Atualiza o botão de enviar/microfone
function updateSendButton() {
    const sendBtn = document.querySelector('.send-btn');
    const messageInput = document.getElementById("mensagem");
    
    if (messageInput.value.trim().length > 0) {
        sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
        sendBtn.style.backgroundColor = 'var(--whatsapp-green)';
    } else {
        sendBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        sendBtn.style.backgroundColor = 'var(--whatsapp-teal-green)';
    }
}

// Ajusta o layout quando o teclado aparece
function handleKeyboard() {
    const visualViewport = window.visualViewport;
    const inputContainer = document.querySelector('.input-container');
    
    if (visualViewport) {
        const viewportHeight = visualViewport.height;
        const windowHeight = window.innerHeight;
        const keyboardHeight = windowHeight - viewportHeight;
        
        if (keyboardHeight > 0) {
            inputContainer.style.transform = `translateY(-${keyboardHeight}px)`;
        } else {
            inputContainer.style.transform = 'translateY(0)';
        }
        
        scrollToBottom();
    }
}

// Inicialização
function init() {
    const form = document.getElementById("mensagem-form");
    if (form) {
        form.addEventListener("submit", sendMessage);
    }
    
    document.getElementById("mensagem").addEventListener("input", updateSendButton);
    
    if (window.visualViewport) {
        window.visualViewport.addEventListener('resize', handleKeyboard);
    }
    
    window.addEventListener('resize', adjustChatHeight);  // Usando adjustChatHeight diretamente
    
    document.getElementById("mensagem").focus();
    
    adjustChatHeight();
}

// Ajusta a altura da área de chat
function adjustChatHeight() {
    const header = document.querySelector('header');
    const inputContainer = document.querySelector('.input-container');
    const chatArea = document.getElementById('chat-box');
    
    if (header && inputContainer && chatArea) {
        const headerHeight = header.offsetHeight;
        const inputHeight = inputContainer.offsetHeight;
        
        chatArea.style.height = `calc(100vh - ${headerHeight}px - ${inputHeight}px)`;
        scrollToBottom();
    }
}

document.addEventListener("DOMContentLoaded", init);
// Ampliar imagem de perfil ao clicar
document.querySelector('.avatar img').addEventListener('click', () => {
    const overlay = document.createElement('div');
    overlay.className = 'image-overlay';
    overlay.innerHTML = `
        <div class="image-container">
            <img src="static/img/clara_avatar.png" alt="Clara em tamanho maior" />
        </div>
    `;
    overlay.addEventListener('click', () => document.body.removeChild(overlay));
    document.body.appendChild(overlay);
});
