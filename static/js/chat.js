// Gera ou recupera o user_id do localStorage
function getUserId() {
    let userId = localStorage.getItem('user_id');
    if (!userId) {
        userId = 'user-' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('user_id', userId);
    }
    return userId;
}

// Exibe a mensagem no chat
function displayMessage({ from, text }) {
    const chatBox = document.getElementById("chat-box");
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("mensagem", from === "me" ? "minha" : "dela");
    messageDiv.innerHTML = `<p>${text}</p>`;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Envia mensagem manualmente
function sendMessage(event) {
    event.preventDefault();

    const messageInput = document.getElementById("mensagem");
    const message = messageInput.value.trim();
    if (message === "") return;

    displayMessage({ from: "me", text: message });
    messageInput.value = "";

    const userId = getUserId();

    fetch("/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mensagem: message, user_id: userId })
    })
        .then(response => response.json())
        .then(data => {
            displayMessage({ from: "clara", text: data.resposta });
        })
        .catch(error => {
            console.error("Erro ao enviar mensagem:", error);
        });
}

// Escuta o envio do formulário
document.getElementById("mensagem-form").addEventListener("submit", sendMessage);

// === Verificação automática de novas mensagens da Clara ===
function verificarMensagensNovas() {
    const userId = getUserId();

    fetch(`/mensagens_novas?user_id=${userId}`)
        .then(response => response.json())
        .then(data => {
            if (data.novas && data.novas.length > 0) {
                data.novas.forEach(msg => {
                    displayMessage({ from: "clara", text: msg });
                });
            }
        })
        .catch(err => console.error("Erro ao buscar mensagens novas:", err));
}

// Verifica novas mensagens a cada 15 segundos
setInterval(verificarMensagensNovas, 15000);
