import os
import sqlite3
import requests
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from claraprompt import prompt_clara, prompt_proactive
import pytz
import schedule
import time
import threading

app = Flask(__name__)

# Configuração do fuso horário (GMT-3)
tz = pytz.timezone('America/Sao_Paulo')

# Configuração da API do OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Configuração do banco de dados SQLite
def init_db():
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT,
                  sender TEXT,
                  message TEXT,
                  timestamp TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Função para obter o horário atual em GMT-3
def get_current_time():
    return datetime.now(tz).strftime('%H:%M')

# Função para salvar uma mensagem no banco de dados
def save_message(user_id, sender, message):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO messages (user_id, sender, message, timestamp) VALUES (?, ?, ?, ?)",
              (user_id, sender, message, timestamp))
    conn.commit()
    conn.close()

# Função para recuperar o histórico de mensagens do usuário (limite de 5 mensagens mais recentes)
def get_history(user_id):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("SELECT sender, message FROM messages WHERE user_id = ? ORDER BY timestamp DESC LIMIT 5", (user_id,))
    history = c.fetchall()
    conn.close()
    return history

# Função para enviar mensagem proativa
def send_proactive_message():
    print("Enviando mensagem proativa...")
    
    # Obter o histórico da conversa
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute("SELECT sender, message FROM messages ORDER BY id DESC LIMIT 5")
    history = c.fetchall()
    conn.close()

    # Formatar o histórico para o prompt
    history_text = "\n".join([f"{msg[0]}: {msg[1]}" for msg in history]) if history else "Nenhuma mensagem anterior."

    # Preparar o prompt para mensagem proativa
    current_time = get_current_time()
    messages = [
        {"role": "system", "content": prompt_proactive},
        {"role": "user", "content": f"Horário atual: {current_time} (GMT-3)\nHistórico da conversa:\n{history_text}"}
    ]

    # Enviar requisição para o OpenRouter API
    print("Enviando requisição pro OpenRouter API...")
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "gryphe/mythomax-l2-13b:free",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500
    }
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data
    )

    if response.status_code == 200:
        print("Resposta do OpenRouter API:", response.json())
        clara_response = response.json()['choices'][0]['message']['content']
        
        # Salvar a mensagem proativa no banco de dados
        timestamp = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect('chat_history.db')
        c = conn.cursor()
        c.execute("INSERT INTO messages (sender, message, timestamp) VALUES (?, ?, ?)",
                  ("Clara", clara_response, timestamp))
        conn.commit()
        conn.close()
        print(f"Mensagem proativa enviada: {clara_response}")
    else:
        print(f"Erro ao enviar mensagem proativa: {response.status_code} - {response.text}")

# Função para rodar o agendador em uma thread separada
def run_scheduler():
    # Agendar mensagens proativas em horários específicos (em GMT-3)
    schedule.every().day.at("11:00").do(send_proactive_message)  # Mensagem às 11:00
    schedule.every().day.at("11:30").do(send_proactive_message)  # Mensagem às 11:30

    while True:
        schedule.run_pending()
        time.sleep(60)  # Verifica a cada minuto

# Iniciar o agendador em uma thread separada
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

@app.route('/', methods=['GET'])
def index():
    # Carregar o histórico de mensagens do banco de dados
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute("SELECT sender, message FROM messages ORDER BY id")
    messages = c.fetchall()
    conn.close()
    return render_template('index.html', messages=messages)

@app.route('/', methods=['POST'])
def index_post():
    return jsonify({'error': 'Método POST não permitido neste endpoint. Use /send_message para enviar mensagens.'}), 405

@app.route('/clara', methods=['POST'])
def conversar_com_clara():
    data = request.get_json()
    mensagem = data.get('mensagem')
    user_id = data.get('user_id', "default_user")  # Define um user_id padrão se não for fornecido

    if not mensagem:
        return jsonify({'erro': 'Mensagem não fornecida'}), 400

    # Obtém o horário atual no fuso GMT-3
    current_time = get_current_time()

    # Recupera o histórico de mensagens
    history = get_history(user_id)
    history_text = "\n".join([f"{sender}: {msg}" for sender, msg in reversed(history)]) if history else "Nenhuma mensagem anterior."

    # Monta o prompt no formato de mensagens para o OpenRouter
    messages = [
        {"role": "system", "content": prompt_clara},
        {"role": "user", "content": f"Horário atual: {current_time} (GMT-3)\nHistórico da conversa:\n{history_text}\nUsuário: {mensagem}"}
    ]

    # Enviar requisição para o OpenRouter API
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "gryphe/mythomax-l2-13b:free",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500
    }
    try:
        print("Enviando requisição pro OpenRouter API...")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=5
        )
        print("Resposta do OpenRouter API:", response.status_code, response.text)
        resposta = response.json()

        # Extrai a resposta do modelo
        clara_response = resposta["choices"][0]["message"]["content"]

        # Salva a mensagem do usuário e a resposta da Clara no banco de dados
        save_message(user_id, "user", mensagem)
        save_message(user_id, "Clara", clara_response)

        return jsonify({'resposta': clara_response})
    except requests.Timeout:
        print("Erro: Timeout na requisição pro OpenRouter API")
        return jsonify({'erro': 'A Clara tá demorando pra responder. Tenta de novo?'}), 500
    except Exception as e:
        print("Erro ao processar resposta do OpenRouter:", str(e))
        return jsonify({'erro': 'A Clara teve dificuldade em responder agora. Tenta de novo?'}), 500

@app.route('/send_message', methods=['POST'])
def send_message():
    user_message = request.form['message']
    user_id = "default_user"  # Define um user_id padrão para o frontend

    # Salvar a mensagem do usuário no banco de dados
    save_message(user_id, "Você", user_message)

    # Obter o histórico das últimas 5 mensagens
    history = get_history(user_id)
    history_text = "\n".join([f"{msg[0]}: {msg[1]}" for msg in history]) if history else "Nenhuma mensagem anterior."

    # Preparar o prompt para o OpenRouter API
    current_time = get_current_time()
    messages = [
        {"role": "system", "content": prompt_clara},
        {"role": "user", "content": f"Horário atual: {current_time} (GMT-3)\nHistórico da conversa:\n{history_text}\nUsuário: {user_message}"}
    ]

    # Enviar requisição para o OpenRouter API
    print("Enviando requisição pro OpenRouter API...")
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "gryphe/mythomax-l2-13b:free",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500
    }
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=5
        )
        print("Resposta do OpenRouter API:", response.status_code, response.text)
        resposta = response.json()

        # Extrai a resposta do modelo
        clara_response = resposta["choices"][0]["message"]["content"]

        # Salvar a resposta da Clara no banco de dados
        save_message(user_id, "Clara", clara_response)

        return jsonify({'response': clara_response})
    except requests.Timeout:
        print("Erro: Timeout na requisição pro OpenRouter API")
        return jsonify({'error': 'A Clara tá demorando pra responder. Tenta de novo?'}), 500
    except Exception as e:
        print("Erro ao processar resposta do OpenRouter:", str(e))
        return jsonify({'error': 'A Clara teve dificuldade em responder agora. Tenta de novo?'}), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)