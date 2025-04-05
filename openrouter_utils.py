import os
import requests
import sqlite3
import importlib
from datetime import datetime
import pytz
from dotenv import load_dotenv
from prompt_builder import build_prompt

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").replace('\n', '').replace('\r', '').strip()

print("🔑 OPENROUTER_API_KEY carregada")

# Inicializa o banco de dados
def init_db():
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            user_id TEXT,
            sender TEXT,
            message TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

# Salva uma mensagem no banco
def save_message(user_id, sender, message):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    timestamp = datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO messages (user_id, sender, message, timestamp) VALUES (?, ?, ?, ?)",
              (user_id, sender, message, timestamp))
    conn.commit()
    conn.close()

# Recupera o histórico do usuário (últimas 5 mensagens)
def get_history(user_id):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("SELECT sender, message FROM messages WHERE user_id = ? ORDER BY timestamp DESC LIMIT 5", (user_id,))
    history = c.fetchall()
    conn.close()
    return history

# Gera resposta da Clara com prompt dinâmico
def gerar_resposta_clara(mensagem_usuario, user_id="local_user"):
    if not OPENROUTER_API_KEY:
        print("Erro: OPENROUTER_API_KEY não configurada!")
        return "⚠️ A Clara não conseguiu responder agora. Tenta mais tarde?"

    init_db()
    save_message(user_id, "Usuário", mensagem_usuario)

    fuso_horario = pytz.timezone("America/Sao_Paulo")
    horario_atual = datetime.now(fuso_horario).strftime("%H:%M")

    historico = get_history(user_id)
    history_text = "\n".join([f"{s}: {m}" for s, m in reversed(historico)])

    # Memórias fixas por enquanto (pode ser dinâmico depois)
    memorias = [
        "Ele gosta de carinho antes de dormir",
        "Trabalha como motorista",
        "Fica mais carente à noite"
    ]

    # Define o estado da conversa (normal ou sexual)
    estado = "normal"

    # Constrói o prompt dinâmico
    prompt_dinamico = build_prompt("André", estado, memorias, historico=history_text, hora=horario_atual)

    mensagens_formatadas = [
        {"role": "system", "content": prompt_dinamico},
        {"role": "user", "content": mensagem_usuario}
    ]

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "deepseek/deepseek-chat-v3-0324:free",
        "messages": mensagens_formatadas
    }

    try:
        print("Enviando requisição pro OpenRouter...")
        response = requests.post(url, headers=headers, json=data, timeout=10)
        resposta = response.json()
        print("📨 Resposta da API completa:", resposta)

        reply = resposta["choices"][0]["message"]["content"]

        save_message(user_id, "Clara", reply)
        return reply

    except requests.Timeout:
        print("⏱️ Timeout na requisição pro OpenRouter")
        return "⏱️ A Clara demorou demais pra responder. Tenta de novo?"

    except Exception as e:
        print("❌ Erro ao processar resposta da Clara:", str(e), resposta if 'resposta' in locals() else "Sem resposta")
        return "⚠️ A Clara teve um problema técnico. Tenta de novo?"

