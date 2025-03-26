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

// Função pra enviar mensagem
function sendMessage(event) {
    event.preventDefault(); // Impede o comportamento padrão do formulário

    const messageInput = document.getElementById("mensagem");
    const message = messageInput.value.trim();
    if (message === "") return;

    displayMessage({ from: "me", text: message });
    messageInput.value = "";

    const userId = getUserId(); // Pega o user_id

    fetch("/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mensagem: message, user_id: userId }) // Inclui o user_id
    })
        .then(response => response.json())
        .then(data => {
            displayMessage({ from: "her", text: data.resposta });
        })
        .catch(error => {
            console.error("Erro:", error);
            displayMessage({ from: "her", text: "⚠️ A Clara teve um problema. Tenta de novo?" });
        });
}

// Função pra exibir mensagens
function displayMessage(message) {
    const chatBox = document.getElementById("chat-box");
    const msgDiv = document.createElement("div");
    msgDiv.className = message.from === "me" ? "message user-message" : "message clara-message";
    msgDiv.textContent = message.text;

    // Adiciona o timestamp
    const timestampDiv = document.createElement("div");
    timestampDiv.className = "timestamp";
    timestampDiv.textContent = getCurrentTime(); // Função para obter a hora atual
    msgDiv.appendChild(timestampDiv);

    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function getCurrentTime() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
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