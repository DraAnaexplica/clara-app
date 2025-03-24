import os
import requests
import sqlite3
from claraprompt import prompt_clara

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def init_db():
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS history (user_id TEXT, message TEXT, response TEXT)")
    conn.commit()
    conn.close()

def save_message(user_id, message, response):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("INSERT INTO history (user_id, message, response) VALUES (?, ?, ?)", (user_id, message, response))
    conn.commit()
    conn.close()

def get_history(user_id):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("SELECT message, response FROM history WHERE user_id = ? ORDER BY rowid DESC LIMIT 5", (user_id,))
    history = c.fetchall()
    conn.close()
    return history

init_db()

def gerar_resposta_clara(mensagem_usuario, user_id="default_user"):
    history = get_history(user_id)
    history_text = "\n".join([f"Usuário: {msg} | Clara: {resp}" for msg, resp in history])

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "contents": [{
            "parts": [{
                "text": prompt_clara + "\nHistórico recente:\n" + history_text + "\nUsuário: " + mensagem_usuario
            }]
        }]
    }

    response = requests.post(f"{url}?key={GEMINI_API_KEY}", headers=headers, json=data)
    resposta = response.json()

    try:
        reply = resposta["candidates"][0]["content"]["parts"][0]["text"]
        save_message(user_id, mensagem_usuario, reply)
        return reply
    except Exception:
        return "⚠️ A Clara teve dificuldade em responder agora. Tenta de novo?"



