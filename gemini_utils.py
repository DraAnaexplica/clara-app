import os
import requests
import sqlite3
from core.validation.response_validator import validate  # 👈 Novo import
from claraprompt import prompt_clara
from datetime import datetime
import pytz
from dotenv import load_dotenv
load_dotenv()

print("🔑 GEMINI_API_KEY carregada:", os.getenv("GEMINI_API_KEY"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

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
    c.execute("SELECT sender, message FROM messages WHERE user_id = ? ORDER BY timestamp DESC LIMIT 5", (user_id,))
    history = c.fetchall()
    conn.close()
    return history

def gerar_resposta_clara_gemini(mensagem_usuario, user_id=""):
    if not GEMINI_API_KEY:
        print("❌ Erro: GEMINI_API_KEY não configurada!")
        return "⚠️ Clara não conseguiu responder agora. Tenta mais tarde?"

    init_db()
    if user_id:
        save_message(user_id, "Usuário", mensagem_usuario)

    fuso_horario = pytz.timezone("America/Sao_Paulo")
    horario_atual = datetime.now(fuso_horario).strftime("%H:%M")

    historico = get_history(user_id) if user_id else []
    history_text = "\n".join([f"{sender}: {msg}" for sender, msg in reversed(historico)])
    if not history_text:
        history_text = "Nenhuma mensagem anterior."

    prompt_final = f"""
    Horário atual: {horario_atual} (GMT-3)

    Histórico da conversa:
    {history_text}

    {prompt_clara}
    """

    headers = { "Content-Type": "application/json" }
    data = {
        "contents": [{
            "parts": [{ "text": prompt_final }]
        }]
    }

    try:
        print("📱 Enviando requisição pro Gemini...")
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}",
            headers=headers,
            json=data,
            timeout=10
        )

        if response.status_code == 200:
            resultado = response.json()
            reply = resultado["candidates"][0]["content"]["parts"][0]["text"]

            if user_id:
                save_message(user_id, "Clara", reply)

return validate(reply)  # 👈 Aplica o validador
        else:
            print(f"⚠️ Erro {response.status_code}: {response.text}")
            return "⚠️ Clara não conseguiu responder agora. Tenta de novo?"
    except requests.Timeout:
        return "⏱️ A Clara demorou demais pra responder. Tenta de novo?"
    except Exception as e:
        print("Erro inesperado:", str(e))
        return "⚠️ A Clara teve um problema técnico. Tenta de novo?"




