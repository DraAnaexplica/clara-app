import os
import requests
import sqlite3
from claraprompt import prompt_clara
from datetime import datetime
import pytz  # Biblioteca pra lidar com fuso horário

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Inicializa o banco de dados SQLite
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

# Salva uma mensagem no banco de dados
def save_message(user_id, sender, message):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    timestamp = datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO messages (user_id, sender, message, timestamp) VALUES (?, ?, ?, ?)",
              (user_id, sender, message, timestamp))
    conn.commit()
    conn.close()

# Recupera o histórico de mensagens do usuário (limite de 5 mensagens mais recentes)
def get_history(user_id):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("SELECT sender, message FROM messages WHERE user_id = ? ORDER BY timestamp DESC LIMIT 5", (user_id,))
    history = c.fetchall()
    conn.close()
    return history

def gerar_resposta_clara(mensagem_usuario, user_id=""):
    if not GEMINI_API_KEY:
        print("Erro: GEMINI_API_KEY não configurada!")
        return "⚠️ A Clara teve dificuldade em responder agora. Tenta de novo?"

    # Inicializa o banco de dados (se ainda não foi inicializado)
    init_db()

    # Salva a mensagem do usuário no banco de dados
    if user_id:
        save_message(user_id, "user", mensagem_usuario)

    # Obtém o horário atual no fuso GMT-3
    fuso_horario = pytz.timezone("America/Sao_Paulo")  # GMT-3
    horario_atual = datetime.now(fuso_horario).strftime("%H:%M")

    # Recupera o histórico de mensagens
    history = get_history(user_id) if user_id else []
    history_text = "\n".join([f"{sender}: {msg}" for sender, msg in reversed(history)])

    url = url = url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "contents": [{
            "parts": [{
                "text": f"{prompt_clara}\nHistórico da conversa:\n{history_text}\nHorário atual: {horario_atual} (GMT-3)\nUsuário: {mensagem_usuario}"
            }]
        }]
    }

    try:
        print("Enviando requisição pro Gemini API...")
        response = requests.post(f"{url}?key={GEMINI_API_KEY}", headers=headers, json=data, timeout=5)
        print("Resposta do Gemini API:", response.status_code, response.text)
        resposta = response.json()

        reply = resposta["candidates"][0]["content"]["parts"][0]["text"]

        # Salva a resposta da Clara no banco de dados
        if user_id:
            save_message(user_id, "Clara", reply)

        return reply
    except requests.Timeout:
        print("Erro: Timeout na requisição pro Gemini API")
        return "⚠️ A Clara tá demorando pra responder. Tenta de novo?"
    except Exception as e:
        print("Erro ao processar resposta do Gemini:", str(e), resposta if 'resposta' in locals() else "Sem resposta")
        return "⚠️ A Clara teve dificuldade em responder agora. Tenta de novo?"

