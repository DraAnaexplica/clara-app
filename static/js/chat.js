document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("mensagem-form");
    const input = document.getElementById("mensagem");
    const chatBox = document.getElementById("chat-box");

    form.addEventListener("submit", async function (e) {
        e.preventDefault();
        const mensagem = input.value.trim();
        if (!mensagem) return;

        adicionarMensagem("Você", mensagem, "user");

        const response = await fetch("/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ mensagem: mensagem })
        });

        const data = await response.json();
        adicionarMensagem("Clara", data.resposta, "clara");

        input.value = "";
        chatBox.scrollTop = chatBox.scrollHeight;
    });

    function adicionarMensagem(remetente, texto, classe) {
        const div = document.createElement("div");
        div.classList.add("message", classe);
        div.innerHTML = `<strong>${remetente}:</strong> ${texto}`;
        chatBox.appendChild(div);
    }
});

