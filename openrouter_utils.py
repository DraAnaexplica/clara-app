import os
import sqlite3
import requests
from datetime import datetime
import pytz
from claraprompt import prompt_clara

# Configuração do OpenRouter
MODEL = "gryphe/mythonax-12-13b"  # Modelo gratuito
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")  # Chave no Render

def init_db():
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  sender TEXT,
                  message TEXT,
                  timestamp TEXT)''')
    conn.commit()
    conn.close()

def save_message(sender, message):
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    timestamp = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO messages (sender, message, timestamp) VALUES (?, ?, ?)",
              (sender, message, timestamp))
    conn.commit()
    conn.close()

def get_history(limit=5):
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute("SELECT sender, message FROM messages ORDER BY id DESC LIMIT ?", (limit,))
    history = c.fetchall()
    conn.close()
    return history

def gerar_resposta_clara(mensagem_usuario, user_id=""):
    if not OPENROUTER_API_KEY:
        return "⚠️ Erro: Chave OpenRouter não configurada no Render."

    init_db()
    save_message("Usuário", mensagem_usuario)

    # Formatação do prompt para MythoMax (Llama 2)
    history = get_history()
    history_text = "\n".join([f"{sender}: {msg}" for sender, msg in history])
    current_time = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%H:%M')

    full_prompt = f"""
    [INST] <<SYS>>
    {prompt_clara}
    <</SYS>>

    Histórico:
    {history_text}

    Horário: {current_time} (GMT-3)
    Usuário: {mensagem_usuario}
    [/INST]
    """

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": full_prompt}],
                "temperature": 0.7,
                "max_tokens": 800
            },
            timeout=15
        )
        resposta = response.json()
        clara_response = resposta["choices"][0]["message"]["content"]
        save_message("Clara", clara_response)
        return clara_response

    except Exception as e:
        print(f"Erro no OpenRouter: {str(e)}")
        return "⚠️ Clara está ocupada. Tente novamente mais tarde!"

