// Função para enviar mensagem
function sendMessage(event) {
    event.preventDefault();

    const messageInput = document.getElementById("mensagem");
    const message = messageInput.value.trim();
    if (message === "") return;

    displayMessage({ from: "me", text: message, timestamp: getTimestamp() });
    messageInput.value = "";

    const userId = getUserId();

    fetch("/send_message", {  // Alterado de "/" para "/send_message"
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mensagem: message, user_id: userId })
    })
    .then(response => {
        if (!response.ok) throw new Error("Erro na resposta do servidor");
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