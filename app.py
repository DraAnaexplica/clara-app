import os
import sqlite3
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from claraprompt import prompt_clara, prompt_proactive
import pytz
import schedule
import time
import threading

app = Flask(__name__)

tz = pytz.timezone('America/Sao_Paulo')

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

def get_current_time():
    return datetime.now(tz).strftime('%H:%M')

def send_proactive_message():
    print("Enviando mensagem proativa...")
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute("SELECT sender, message FROM messages ORDER BY id DESC LIMIT 5")
    history = c.fetchall()
    conn.close()

    history_text = "\n".join([f"{msg[0]}: {msg[1]}" for msg in history]) or "Nenhuma mensagem anterior."
    current_time = get_current_time()
    full_prompt = f"""
    Horário atual: {current_time} (GMT-3)
    Histórico da conversa:
    {history_text}
    {prompt_proactive}
    """

    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": full_prompt}]}]}
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Erro: GEMINI_API_KEY não configurada!")
        return
    
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}",
        headers=headers,
        json=data
    )

    if response.status_code == 200:
        clara_response = response.json()['candidates'][0]['content']['parts'][0]['text']
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
    data = request.get_json()
    user_message = data.get('mensagem')
    user_id = data.get('user_id')
    
    timestamp = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (sender, message, timestamp) VALUES (?, ?, ?)",
              ("Você", user_message, timestamp))
    conn.commit()

    c.execute("SELECT sender, message FROM messages ORDER BY id DESC LIMIT 5")
    history = c.fetchall()
    conn.close()

    history_text = "\n".join([f"{msg[0]}: {msg[1]}" for msg in history]) or "Nenhuma mensagem anterior."
    current_time = get_current_time()
    full_prompt = f"""
    Horário atual: {current_time} (GMT-3)
    Histórico da conversa:
    {history_text}
    {prompt_clara}
    """

    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": full_prompt}]}]}
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return jsonify({'error': 'API key não configurada'}), 500
    
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}",
        headers=headers,
        json=data
    )

    if response.status_code == 200:
        clara_response = response.json()['candidates'][0]['content']['parts'][0]['text']
        timestamp = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect('chat_history.db')
        c = conn.cursor()
        c.execute("INSERT INTO messages (sender, message, timestamp) VALUES (?, ?, ?)",
                  ("Clara", clara_response, timestamp))
        conn.commit()
        conn.close()
        return jsonify({'resposta': clara_response})
    else:
        return jsonify({'error': 'Erro ao processar a mensagem'}), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)