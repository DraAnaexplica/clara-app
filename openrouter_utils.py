import os
import requests
import sqlite3
from claraprompt import prompt_clara
from datetime import datetime
import pytz

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Banco de dados
def init_db():
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS messages (
        user_id TEXT,
        sender TEXT,
        message TEXT,
        timestamp TEXT
    )""")
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
    c.execute("SELECT sender, message FROM messages WHERE user_id = ? ORDER BY timestamp DESC LIMIT 5", (user_id,))
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

    history = get_history(user_id) if user_id else []
    mensagens_formatadas = [
        {"role": "system", "content": prompt_clara},
    ]

    # Adiciona histórico
    for sender, msg in reversed(history):
        mensagens_formatadas.append({
            "role": "user" if sender.lower() == "usuário" else "assistant",
            "content": msg
        })

    # Adiciona a nova mensagem do usuário
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
        "model": "openai/gpt-3.5-turbo",  # ou "mistralai/mistral-7b-instruct", etc.
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
