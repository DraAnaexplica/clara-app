function getUserId() {
    let userId = localStorage.getItem('user_id');
    if (!userId) {
        userId = 'user-' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('user_id', userId);
    }
    return userId;
}

function getTimestamp() {
    const now = new Date();
    return now.getHours().toString().padStart(2, '0') + ':' + 
           now.getMinutes().toString().padStart(2, '0');
}

function sendMessage(event) {
    event.preventDefault();

    const messageInput = document.getElementById("mensagem");
    const message = messageInput.value.trim();
    if (message === "") return;

    displayMessage({ from: "me", text: message, timestamp: getTimestamp() });
    messageInput.value = "";

    const userId = getUserId();

    console.log("Enviando mensagem:", { mensagem: message, user_id: userId });  // Log para depuração
    fetch("/send_message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mensagem: message, user_id: userId })
    })
    .then(response => {
        console.log("Resposta do servidor:", response);  // Log para depuração
        if (!response.ok) throw new Error(`Erro ${response.status}: ${response.statusText}`);
        return response.json();
    })
    .then(data => {
        console.log("Dados recebidos:", data);  // Log para depuração
        displayMessage({ from: "her", text: data.resposta, timestamp: getTimestamp() });
    })
    .catch(error => {
        console.error("Erro ao enviar mensagem:", error);  // Log mais detalhado
        displayMessage({ 
            from: "her", 
            text: "⚠️ Desculpe, algo deu errado. Tente novamente!", 
            timestamp: getTimestamp() 
        });
    });
}

function displayMessage(message) {
    const chatBox = document.getElementById("chat-box");
    const msgDiv = document.createElement("div");
    msgDiv.className = message.from === "me" ? "message user-message" : "message clara-message";
    msgDiv.textContent = message.text;

    const timestampSpan = document.createElement("span");
    timestampSpan.className = "timestamp";
    timestampSpan.textContent = message.timestamp;
    msgDiv.appendChild(timestampSpan);

    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("mensagem-form");
    if (form) {
        form.addEventListener("submit", sendMessage);
    } else {
        console.error("Formulário com ID 'mensagem-form' não encontrado!");
    }
});