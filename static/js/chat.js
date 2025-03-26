// Gera ou recupera o user_id do localStorage
function getUserId() {
    let userId = localStorage.getItem('user_id');
    if (!userId) {
        // Gera um UUID simples
        userId = 'user-' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('user_id', userId);
    }
    return userId;
}

// Função para formatar o timestamp
function getTimestamp() {
    const now = new Date();
    return now.getHours().toString().padStart(2, '0') + ':' + 
           now.getMinutes().toString().padStart(2, '0');
}

// Função para enviar mensagem
function sendMessage(event) {
    event.preventDefault(); // Impede o comportamento padrão do formulário

    const messageInput = document.getElementById("mensagem");
    const message = messageInput.value.trim();
    if (message === "") return;

    // Exibe a mensagem do usuário imediatamente
    displayMessage({ from: "me", text: message, timestamp: getTimestamp() });
    messageInput.value = "";

    const userId = getUserId(); // Pega o user_id

    fetch("/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mensagem: message, user_id: userId })
    })
        .then(response => {
            if (!response.ok) {
                throw new Error("Erro na resposta do servidor");
            }
            return response.json();
        })
        .then(data => {
            displayMessage({ from: "her", text: data.resposta, timestamp: getTimestamp() });
        })
        .catch(error => {
            console.error("Erro:", error);
            displayMessage({ 
                from: "her", 
                text: "⚠️ Desculpe, algo deu errado. Tente novamente!", 
                timestamp: getTimestamp() 
            });
        });
}

// Função para exibir mensagens
function displayMessage(message) {
    const chatBox = document.getElementById("chat-box");
    const msgDiv = document.createElement("div");
    msgDiv.className = message.from === "me" ? "message user-message" : "message clara-message";
    msgDiv.textContent = message.text;

    // Adiciona o timestamp
    const timestampSpan = document.createElement("span");
    timestampSpan.className = "timestamp";
    timestampSpan.textContent = message.timestamp;
    msgDiv.appendChild(timestampSpan);

    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight; // Rolagem automática
}

// Garante que o DOM esteja carregado antes de adicionar o evento
document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("mensagem-form");
    if (form) {
        form.addEventListener("submit", sendMessage);
    } else {
        console.error("Formulário com ID 'mensagem-form' não encontrado!");
    }
});