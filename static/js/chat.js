document.getElementById("chat-form").addEventListener("submit", async function (e) {
    e.preventDefault();

    const input = document.getElementById("user-input");
    const message = input.value.trim();
    if (!message) return;

    appendMessage("user-message", message);
    input.value = "";

    try {
        const response = await fetch("/", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: "message=" + encodeURIComponent(message)
        });

        const data = await response.text();
        appendMessage("clara-message", data);
    } catch (error) {
        appendMessage("clara-message", "❌ Erro ao enviar a mensagem.");
    }
});

function appendMessage(className, text) {
    const chatBox = document.getElementById("chat-box");
    const messageDiv = document.createElement("div");
    messageDiv.className = className;
    messageDiv.textContent = text;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Função para ampliar imagem
function ampliarImagem() {
    document.getElementById("imagem-ampliada").style.display = "block";
}

// Função para fechar imagem ampliada
function fecharImagem() {
    document.getElementById("imagem-ampliada").style.display = "none";
}
