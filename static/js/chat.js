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

// Função pra enviar mensagem (ajustada)
function sendMessage() {
    const messageInput = document.getElementById("message-input");
    const message = messageInput.value.trim();
    if (message === "") return;

    displayMessage({ from: "me", text: message });
    messageInput.value = "";

    const userId = getUserId(); // Pega o user_id

    fetch("/clara", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mensagem: message, user_id: userId }) // Envia o user_id
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

// Função pra exibir mensagens (já existente)
function displayMessage(message) {
    const chatBox = document.getElementById("chat-box");
    const msgDiv = document.createElement("div");
    msgDiv.className = message.from === "me" ? "message me" : "message her";
    msgDiv.textContent = message.text;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Chama sendMessage ao clicar no botão ou pressionar Enter (exemplo)
document.getElementById("send-button").addEventListener("click", sendMessage);
document.getElementById("message-input").addEventListener("keypress", function (e) {
    if (e.key === "Enter") sendMessage();
});
