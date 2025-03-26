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
    document.querySelector('.send-btn').innerHTML = '<i class="fas fa-microphone"></i>';
    
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

// Alternar entre microfone e ícone de enviar
document.getElementById("mensagem").addEventListener("input", function(e) {
    const sendBtn = document.querySelector('.send-btn');
    if (e.target.value.trim().length > 0) {
        sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
    } else {
        sendBtn.innerHTML = '<i class="fas fa-microphone"></i>';
    }
});

// Event Listeners
document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("mensagem-form");
    if (form) {
        form.addEventListener("submit", sendMessage);
    }
    
    // Mensagem inicial da Clara
    setTimeout(() => {
        displayMessage({
            from: "her",
            text: "Olá! Eu sou a Clara. Como posso te ajudar hoje?"
        });
    }, 500);
});