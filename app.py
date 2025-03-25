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

    # Enviar requisição para o Gemini API
    print("Enviando requisição pro Gemini API...")
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "contents": [{
            "parts": [{
                "text": full_prompt
            }]
        }]
    }
    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=" + os.getenv("GEMINI_API_KEY"),
        headers=headers,
        json=data
    )

    if response.status_code == 200:
        print("Resposta do Gemini API:", response.json())
        clara_response = response.json()['candidates'][0]['content']['parts'][0]['text']
        
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
    schedule.every().day.at("09:00").do(send_proactive_message)  # Mensagem matinal
    schedule.every().day.at("14:00").do(send_proactive_message)  # Mensagem à tarde
    schedule.every().day.at("20:00").do(send_proactive_message)  # Mensagem noturna

    while True:
        schedule.run_pending()
        time.sleep(60)  # Verifica a cada minuto

# Iniciar o agendador em uma thread separada
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

@app.route('/')
def index():
    # Carregar o histórico de mensagens do banco de dados
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute("SELECT sender, message FROM messages ORDER BY id")
    messages = c.fetchall()
    conn.close()
    return render_template('index.html', messages=messages)

@app.route('/send_message', methods=['POST'])
def send_message():
    user_message = request.form['message']
    
    # Salvar a mensagem do usuário no banco de dados
    timestamp = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (sender, message, timestamp) VALUES (?, ?, ?)",
              ("Você", user_message, timestamp))
    conn.commit()

    # Obter o histórico das últimas 5 mensagens
    c.execute("SELECT sender, message FROM messages ORDER BY id DESC LIMIT 5")
    history = c.fetchall()
    conn.close()

    # Formatar o histórico para o prompt
    history_text = "\n".join([f"{msg[0]}: {msg[1]}" for msg in history])
    if not history_text:
        history_text = "Nenhuma mensagem anterior."

    # Preparar o prompt para o Gemini API
    current_time = get_current_time()
    full_prompt = f"""
    Horário atual: {current_time} (GMT-3)

    Histórico da conversa:
    {history_text}

    {prompt_clara}
    """

    # Enviar requisição para o Gemini API
    print("Enviando requisição pro Gemini API...")
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "contents": [{
            "parts": [{
                "text": full_prompt
            }]
        }]
    }
    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=" + os.getenv("GEMINI_API_KEY"),
        headers=headers,
        json=data
    )

    if response.status_code == 200:
        print("Resposta do Gemini API:", response.json())
        clara_response = response.json()['candidates'][0]['content']['parts'][0]['text']
        
        # Salvar a resposta da Clara no banco de dados
        timestamp = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect('chat_history.db')
        c = conn.cursor()
        c.execute("INSERT INTO messages (sender, message, timestamp) VALUES (?, ?, ?)",
                  ("Clara", clara_response, timestamp))
        conn.commit()
        conn.close()

        return jsonify({'response': clara_response})
    else:
        return jsonify({'error': 'Erro ao processar a mensagem'}), 500

if __name__ == '__main__':
    app.run(debug=True)