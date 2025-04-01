import os
import sqlite3
import requests
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, make_response
from claraprompt import prompt_clara, prompt_proactive
from openrouter_utils import gerar_resposta_clara
import pytz
import schedule
import time
import threading

# Tokens válidos (copiado de routes.py)
TOKENS_VALIDOS = {
    "teste123": {"expira": "2025-04-30"},
    "vip456": {"expira": "2025-05-01"},
}
app = Flask(__name__)

# Configuração do fuso horário (GMT-3)
tz = pytz.timezone('America/Sao_Paulo')

# Configuração do banco de dados SQLite
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

init_db()

# Função para obter o horário atual em GMT-3
def get_current_time():
    return datetime.now(tz).strftime('%H:%M')

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
    history_text = "\n".join([f"{msg[0]}: {msg[1]}" for msg in history])
    if not history_text:
        history_text = "Nenhuma mensagem anterior."

    # Preparar o prompt para mensagem proativa
    current_time = get_current_time()
    full_prompt = f"""
    Horário atual: {current_time} (GMT-3)

    Histórico da conversa:
    {history_text}

    {prompt_proactive}
    """

    # Usar a função gerar_resposta_clara do OpenRouter
    try:
        clara_response = gerar_resposta_clara(full_prompt, user_id="proactive")
        # Salvar a mensagem proativa no banco de dados
        timestamp = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect('chat_history.db')
        c = conn.cursor()
        c.execute("INSERT INTO messages (sender, message, timestamp) VALUES (?, ?, ?)",
                  ("Clara", clara_response, timestamp))
        conn.commit()
        conn.close()
        print(f"Mensagem proativa enviada: {clara_response}")
    except Exception as e:
        print(f"Erro ao enviar mensagem proativa: {str(e)}")

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

@app.route('/')
def index():
    # Obter o user_id a partir do token do cookie
    token = request.cookies.get("token_clara")
    if not token or token not in TOKENS_VALIDOS:
        return redirect(url_for("login"))
    
    user_id = token

    # Carregar o histórico de mensagens do banco de dados para o usuário atual
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute("SELECT sender, message FROM messages WHERE user_id = ? ORDER BY id", (user_id,))
    messages = c.fetchall()
    conn.close()
    return render_template('index.html', messages=messages)

@app.route('/send_message', methods=['POST'])
def send_message():
    user_message = request.form['message']
    
    # Obter o user_id a partir do token do cookie
    token = request.cookies.get("token_clara")
    if not token:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    user_id = token

    # Gerar a resposta da Clara usando a função de openrouter_utils.py
    clara_response = gerar_resposta_clara(user_message, user_id=user_id)

    return jsonify({'response': clara_response})

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        token = request.form.get("token", "")
        if token in TOKENS_VALIDOS:
            # Verificar a data de expiração do token
            data_expiracao = datetime.strptime(TOKENS_VALIDOS[token]["expira"], "%Y-%m-%d")
            data_atual = datetime.now()
            if data_atual > data_expiracao:
                return render_template("login.html", erro="Token expirado.")
            
            resp = make_response(redirect(url_for('index')))
            expira_em = datetime.now() + timedelta(days=30)
            resp.set_cookie("token_clara", token, expires=expira_em)
            return resp
        else:
            return render_template("login.html", erro="Token inválido.")
    return render_template("login.html")

if __name__ == '__main__':
    app.run(debug=True)