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
    const form = document.getElement "Não encontrado" no desktop (`draanaexplica.onrender.com`) indica que o Render não está conseguindo localizar o serviço ou a rota solicitada, o que é consistente com os logs anteriores que mostravam um erro **404 Not Found** para a rota `/`. Isso sugere que o Flask não está conseguindo renderizar o `index.html`, provavelmente devido a um problema na estrutura do projeto ou na configuração do Render. Vamos resolver isso e garantir que o app volte a funcionar como antes, além de ajustar o layout para parecer mais com o WhatsApp, como você originalmente pediu.

---

### Análise do problema
1. **Erro 404 na rota `/`**:
   - Os logs do Render mostram que as requisições GET para `/` retornam 404: