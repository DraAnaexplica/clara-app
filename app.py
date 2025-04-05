import os
import sqlite3
import requests
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import pytz
import schedule
import time
import threading
from openrouter_utils import gerar_resposta_clara

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

    mensagem = "Oi, amor... só passei aqui pra dizer que tô com saudade de você. 😘"
    resposta = gerar_resposta_clara(mensagem, user_id="proativo")

    timestamp = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (sender, message, timestamp) VALUES (?, ?, ?)",
              ("Clara", resposta, timestamp))
    conn.commit()
    conn.close()
    print(f"Mensagem proativa enviada: {resposta}")

# Função para rodar o agendador em uma thread separada
def run_scheduler():
    schedule.every().day.at("11:00").do(send_proactive_message)
    schedule.every().day.at("11:30").do(send_proactive_message)
    while True:
        schedule.run_pending()
        time.sleep(60)

scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

@app.route('/')
def index():
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute("SELECT sender, message FROM messages ORDER BY id")
    messages = c.fetchall()
    conn.close()
    return render_template('index.html', messages=messages)

@app.route('/send_message', methods=['POST'])
def send_message():
    user_message = request.form['message']

    timestamp = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (sender, message, timestamp) VALUES (?, ?, ?)",
              ("Você", user_message, timestamp))
    conn.commit()
    conn.close()

    resposta = gerar_resposta_clara(user_message, user_id="local_user")

    timestamp = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (sender, message, timestamp) VALUES (?, ?, ?)",
              ("Clara", resposta, timestamp))
    conn.commit()
    conn.close()

    return jsonify({'response': resposta})

if __name__ == '__main__':
    app.run(debug=True)
