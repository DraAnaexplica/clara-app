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

// Função pra exibir mensagens com estilo WhatsApp
function displayMessage(message) {
    const chatBox = document.getElementById("chat-box");
    const msgDiv = document.createElement("div");
    
    msgDiv.className = `message ${message.from}`;
    msgDiv.innerHTML = `
        <div class="message-content">${message.text}</div>
        <span class="timestamp">${formatTime()}</span>
    `;
    
    chatBox.appendChild(msgDiv);
    scrollToBottom();
}

// Função para rolar para o final do chat
function scrollToBottom() {
    const chatBox = document.getElementById("chat-box");
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Função pra enviar mensagem
function sendMessage(event) {
    event.preventDefault();
    
    const messageInput = document.getElementById("mensagem");
    const message = messageInput.value.trim();
    if (message === "") return;
    
    // Exibe a mensagem do usuário
    displayMessage({ 
        from: "me", 
        text: message 
    });
    
    messageInput.value = "";
    updateSendButton();
    
    const userId = getUserId();
    
    // Envia para o servidor
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
        console.error("Erro:", error);
        displayMessage({ 
            from: "her", 
            text: "⚠️ Ocorreu um erro. Por favor, tente novamente."
        });
    });
}

// Atualiza o botão de enviar/microfone
function updateSendButton() {
    const sendBtn = document.querySelector('.send-btn');
    const messageInput = document.getElementById("mensagem");
    
    if (messageInput.value.trim().length > 0) {
        sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
    } else {
        sendBtn.innerHTML = '<i class="fas fa-microphone"></i>';
    }
}

// Ajusta o layout quando o teclado aparece
function adjustLayout() {
    const chatArea = document.getElementById('chat-box');
    const headerHeight = document.querySelector('header').offsetHeight;
    const inputHeight = document.querySelector('.input-container').offsetHeight;
    
    chatArea.style.height = `calc(100vh - ${headerHeight}px - ${inputHeight}px)`;
    scrollToBottom();
}

// Event Listeners
document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("mensagem-form");
    if (form) {
        form.addEventListener("submit", sendMessage);
    }
    
    // Atualiza o botão quando o texto muda
    document.getElementById("mensagem").addEventListener("input", updateSendButton);
    
    // Ajusta o layout inicialmente e quando a janela é redimensionada
    adjustLayout();
    window.addEventListener('resize', adjustLayout);
    
    // Foca no input quando a página carrega
    document.getElementById("mensagem").focus();
});