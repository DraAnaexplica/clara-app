# openrouter_utils.py (versão atualizada)

import requests
import json
import sqlite3
import datetime

# Sua chave de API do OpenRouter
API_KEY = "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"

# URL da API OpenRouter
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Nome do banco de dados
DB_NAME = "chat_history.db"

# Função para gerar a resposta da Clara
def gerar_resposta_clara(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openrouter/google/gemini-pro",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }

    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
        print("Resposta da API:", response.status_code, response.text)

        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            return "❌ Clara teve dificuldade em responder agora. Tenta de novo?"

    except Exception as e:
        print("Erro ao enviar requisição para o OpenRouter:", str(e))
        return "❌ Clara teve dificuldade técnica. Me avisa o que aconteceu?"

# Função para salvar mensagem no banco de dados
def save_message(user_id, remetente, mensagem):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS mensagens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        remetente TEXT NOT NULL,
        mensagem TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute("INSERT INTO mensagens (user_id, remetente, mensagem) VALUES (?, ?, ?)",
                   (user_id, remetente, mensagem))
    conn.commit()
    conn.close()

# Função para buscar mensagens novas
def get_new_messages(user_id, last_timestamp=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if last_timestamp:
        cursor.execute("SELECT mensagem FROM mensagens WHERE user_id = ? AND remetente = 'Clara' AND timestamp > ?", (user_id, last_timestamp))
    else:
        cursor.execute("SELECT mensagem FROM mensagens WHERE user_id = ? AND remetente = 'Clara'", (user_id,))

    mensagens = [row[0] for row in cursor.fetchall()]
    conn.close()
    return mensagens


