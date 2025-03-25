// Função pra enviar mensagem
function sendMessage(event) {
    event.preventDefault(); // Impede o comportamento padrão do formulário

    const messageInput = document.getElementById("mensagem");
    const message = messageInput.value.trim();
    if (message === "") return;

    displayMessage({ from: "me", text: message });
    messageInput.value = "";

    fetch("/", {  // Muda de "/clara" pra "/"
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mensagem: message }) // Sem user_id
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
    msgDiv.className = message.from === "me" ? "message me" : "message her";
    msgDiv.textContent = message.text;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
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