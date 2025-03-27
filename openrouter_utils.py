import os
import requests
import sqlite3
from claraprompt import prompt_clara
from datetime import datetime
import pytz

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

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

def save_message(user_id, sender, message):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    timestamp = datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO messages (user_id, sender, message, timestamp) VALUES (?, ?, ?, ?)",
              (user_id, sender, message, timestamp))
    conn.commit()
    conn.close()

def get_history(user_id):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    # Aumentado para 8 mensagens para melhor memória de curto prazo
    c.execute("SELECT sender, message FROM messages WHERE user_id = ? ORDER BY timestamp DESC LIMIT 8", (user_id,))
    history = c.fetchall()
    conn.close()
    return history

def gerar_resposta_clara(mensagem_usuario, user_id=""):
    if not OPENROUTER_API_KEY:
        print("Erro: OPENROUTER_API_KEY não configurada!")
        return "⚠️ A Clara não conseguiu responder agora. Tenta mais tarde?"

    init_db()
    if user_id:
        save_message(user_id, "Usuário", mensagem_usuario)

    fuso_horario = pytz.timezone("America/Sao_Paulo")
    horario_atual = datetime.now(fuso_horario).strftime("%H:%M")

    mensagens_formatadas = [
        { "role": "system", "content": prompt_clara }
    ]

    if user_id:
        historico = get_history(user_id)
        for sender, msg in reversed(historico):
            mensagens_formatadas.append({
                "role": "user" if sender.lower() == "usuário" else "assistant",
                "content": msg
            })

    mensagens_formatadas.append({
        "role": "user",
        "content": f"{mensagem_usuario}\n(Horário atual: {horario_atual})"
    })

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
        reply = resposta["choices"][0]["message"]["content"]

        if user_id:
            save_message(user_id, "Clara", reply)

        return reply
    except requests.Timeout:
        print("Erro: Timeout na requisição pro OpenRouter")
        return "⏱️ A Clara demorou demais pra responder. Tenta de novo?"
    except Exception as e:
        print("Erro ao processar resposta da Clara:", str(e), resposta if 'resposta' in locals() else "Sem resposta")
        return "⚠️ A Clara teve um problema técnico. Tenta de novo?"

