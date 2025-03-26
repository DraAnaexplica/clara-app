// Variáveis globais
let emojiPicker = null;
let pickerContainer = null;

// Função para exibir mensagens
function displayMessage(message) {
    const chatBox = document.getElementById("chat-box");
    const msgDiv = document.createElement("div");
    
    msgDiv.className = `message ${message.from}`;
    msgDiv.innerHTML = `
        <div class="message-content">${message.text}</div>
        <span class="timestamp">${formatTime()}</span>
    `;
    
    chatBox.appendChild(msgDiv);
    scrollToBottom();
}

// Função para rolar para o final
function scrollToBottom() {
    const chatBox = document.getElementById("chat-box");
    setTimeout(() => {
        chatBox.scrollTop = chatBox.scrollHeight;
    }, 50);
}

// Função para formatar hora
function formatTime(date = new Date()) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Função para enviar mensagem
function sendMessage(event) {
    if (event && typeof event.preventDefault === 'function') {
        event.preventDefault();
    }
    
    const messageInput = document.getElementById("mensagem");
    const message = messageInput.value.trim();
    if (message === "") return;
    
    displayMessage({ 
        from: "me", 
        text: message 
    });
    
    messageInput.value = "";
    updateSendButton();
    
    // Simulação de resposta (substitua pelo seu código real)
    setTimeout(() => {
        displayMessage({ 
            from: "her", 
            text: "Mensagem recebida! 😊"
        });
    }, 1000);
}

// Atualiza botão de enviar
function updateSendButton() {
    const sendBtn = document.querySelector('.send-btn');
    const messageInput = document.getElementById("mensagem");
    
    if (messageInput.value.trim().length > 0) {
        sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
        sendBtn.style.backgroundColor = 'var(--whatsapp-green)';
    } else {
        sendBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        sendBtn.style.backgroundColor = 'var(--whatsapp-teal-green)';
    }
}

// Inicializa o emoji picker
function initEmojiPicker() {
    pickerContainer = document.createElement('div');
    pickerContainer.className = 'emoji-picker-container';
    document.body.appendChild(pickerContainer);

    emojiPicker = new EmojiMart.Picker({
        parent: pickerContainer,
        onEmojiSelect: (emoji) => {
            const input = document.getElementById('mensagem');
            input.value += emoji.native;
            input.focus();
            
            if (input.value.trim() === emoji.native) {
                setTimeout(() => {
                    sendMessage({ preventDefault: () => {} });
                    input.value = "";
                }, 50);
            }
        },
        locale: 'pt',
        theme: 'light',
        previewPosition: 'none'
    });

    // Fecha o picker ao clicar fora
    document.addEventListener('click', (e) => {
        const emojiBtn = document.getElementById('emoji-picker-btn');
        if (!pickerContainer.contains(e.target) {
            pickerContainer.classList.remove('visible');
            emojiBtn.classList.remove('active');
        }
    });
}

// Alterna o emoji picker
function toggleEmojiPicker(e) {
    e.stopPropagation();
    const btn = document.getElementById('emoji-picker-btn');
    
    pickerContainer.classList.toggle('visible');
    btn.classList.toggle('active');
}

// Inicialização
function init() {
    initEmojiPicker();
    
    document.getElementById('emoji-picker-btn').addEventListener('click', toggleEmojiPicker);
    document.getElementById('mensagem-form').addEventListener('submit', sendMessage);
    document.getElementById('mensagem').addEventListener('input', updateSendButton);
    document.getElementById('mensagem').focus();
}

// Quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', init);