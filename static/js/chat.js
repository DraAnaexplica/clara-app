document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("mensagem-form");
    const input = document.getElementById("mensagem");
    const chatBox = document.getElementById("chat-box");

    form.addEventListener("submit", async function (e) {
        e.preventDefault();
        const mensagem = input.value.trim();
        if (!mensagem) return;

        // Adiciona a mensagem do usuário
        adicionarMensagem(mensagem, "user-message");

        // Envia a mensagem ao backend
        const response = await fetch("/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ mensagem: mensagem })
        });

        const data = await response.json();
        // Adiciona a resposta da Clara
        adicionarMensagem(data.resposta, "clara-message");

        input.value = "";
        chatBox.scrollTop = chatBox.scrollHeight;
    });

    function adicionarMensagem(texto, classe) {
        const div = document.createElement("div");
        div.classList.add("message", classe);

        // Adiciona o texto da mensagem
        const mensagemTexto = document.createElement("span");
        mensagemTexto.textContent = texto;
        div.appendChild(mensagemTexto);

        // Adiciona o timestamp
        const timestamp = document.createElement("span");
        timestamp.classList.add("timestamp");
        const agora = new Date();
        timestamp.textContent = `${agora.getHours()}:${String(agora.getMinutes()).padStart(2, "0")}`;
        div.appendChild(timestamp);

        chatBox.appendChild(div);
    }
});

