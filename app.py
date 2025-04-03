import os
import sqlite3
import requests # Necessário para send_proactive_message
import json     # Necessário para send_proactive_message
from datetime import datetime, timedelta # Importa timedelta também
# <<< Garantir que redirect e url_for estão importados >>>
from flask import Flask, request, jsonify, render_template, redirect, url_for, make_response, session 
import pytz     # Necessário para send_proactive_message
import schedule # Necessário para run_scheduler
import time     # Necessário para run_scheduler
import threading # Necessário para run_scheduler

# --- Importações das suas lógicas ---
try:
    from claraprompt import prompt_proactive 
except ImportError:
    print("AVISO: Arquivo claraprompt.py ou variável prompt_proactive não encontrado.")
    prompt_proactive = "Instrução proativa padrão." 

try:
    from openrouter_utils import gerar_resposta_clara 
except ImportError:
    print("ERRO CRÍTICO: Arquivo openrouter_utils.py ou função gerar_resposta_clara não encontrado.")
    def gerar_resposta_clara(mensagem_usuario, user_id=None): return "Erro: Módulo de resposta não encontrado." # Adicionado user_id opcional

# --- Configuração do App Flask ---
app = Flask(__name__)
# Considere adicionar: app.secret_key = os.urandom(24)

# Tokens válidos 
TOKENS_VALIDOS = {
    "teste123": {"expira": "2025-04-30"}, 
    "vip456": {"expira": "2025-05-01"},
}

# Configuração do fuso horário 
tz = pytz.timezone('America/Sao_Paulo')

# --- Configuração do Banco de Dados --- 
DATABASE = 'chat_history.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  sender TEXT NOT NULL,
                  message TEXT NOT NULL,
                  timestamp TEXT NOT NULL)''') 
    conn.commit()
    conn.close()

init_db() 

# --- Funções de Mensagem Proativa --- 
def get_current_time_str():
    return datetime.now(tz).strftime('%H:%M')

def send_proactive_message():
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("Erro: GEMINI_API_KEY não configurada para msg proativa.")
        return
    print(f"[{datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')}] Tentando enviar msg proativa...")
    history_text = "Nenhuma mensagem anterior."
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT sender, message FROM messages ORDER BY id DESC LIMIT 10") 
        history = c.fetchall()[::-1] 
        conn.close()
        if history: history_text = "\n".join([f"{s}: {m}" for s, m in history])
    except Exception as e: print(f"Erro DB proativo: {e}")
    current_time = get_current_time_str()
    full_prompt = f"Contexto:\n{history_text}\n\nHorário {current_time} (GMT-3), {prompt_proactive}"
    print("Enviando requisição proativa Gemini...")
    headers = { "Content-Type": "application/json" }
    data = { "contents": [{ "parts": [{ "text": full_prompt }] }] }
    try:
        response = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={gemini_api_key}", headers=headers, json=data, timeout=60 )
        response.raise_for_status() 
        candidates = response.json().get('candidates')
        if candidates and candidates[0].get('content', {}).get('parts'):
            clara_response = candidates[0]['content']['parts'][0]['text'].strip()
            timestamp = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute("INSERT INTO messages (sender, message, timestamp) VALUES (?, ?, ?)", ("Clara", clara_response, timestamp))
            conn.commit()
            conn.close()
            print(f"Msg proativa salva: {clara_response}")
        else: print("Resposta proativa Gemini vazia.")
    except requests.exceptions.RequestException as e: print(f"Erro API proativa: {e}")
    except Exception as e: print(f"Erro inesperado proativo: {e}")

# --- Agendador (Scheduler) --- 
def run_scheduler():
    print("Iniciando agendador...")
    schedule.every().day.at("11:00", tz=tz).do(send_proactive_message) 
    schedule.every().day.at("17:30", tz=tz).do(send_proactive_message) 
    while True:
        try: schedule.run_pending()
        except Exception as e: print(f"Erro agendador: {e}")
        time.sleep(60) 

if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("Thread agendador iniciada.")
else: print("Agendador não iniciado (recarregamento debug).")

# --- Rotas Flask ---

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        token_digitado = request.form.get("token", "")
        if token_digitado in TOKENS_VALIDOS:
            resp = make_response(redirect(url_for('index'))) 
            expira_em = datetime.now(tz) + timedelta(days=30) 
            resp.set_cookie("token_clara", token_digitado, expires=expira_em, httponly=True, samesite='Lax') 
            print(f"Login OK: token={token_digitado}")
            return resp
        else:
            print(f"Login Falhou: token={token_digitado}")
            return render_template("login.html", erro="Token inválido ou expirado.")
    return render_template("login.html")

# --- <<< ROTA INDEX SUBSTITUÍDA E COM DEBUG PRINTS >>> ---
@app.route('/')
def index():
    print("--- ROTA / ACESSADA ---") # Debug Print 1
    token = request.cookies.get("token_clara") 
    print(f"--- TOKEN ENCONTRADO NO COOKIE: {token} ---") # Debug Print 2
    
    # Checa se o token existe e está na lista de válidos
    if not token or token not in TOKENS_VALIDOS:
        print("--- TOKEN INVALIDO/AUSENTE - REDIRECIONANDO PARA LOGIN ---") # Debug Print 3
        return redirect(url_for("login")) 
    
    # Se chegou aqui, o token é válido
    print("--- TOKEN VALIDO - RENDERIZANDO INDEX.HTML ---") # Debug Print 4
    return render_template("index.html") 
# --- <<< FIM DA ROTA INDEX CORRIGIDA >>> ---

@app.route('/clara', methods=['POST'])
def conversar_com_clara():
    # --- <<< ADICIONADO: Verificação de token para a API >>> ---
    token = request.cookies.get("token_clara")
    if not token or token not in TOKENS_VALIDOS:
        print(f"API /clara: Acesso não autorizado (token: {token})")
        return jsonify({'erro': 'Acesso não autorizado'}), 401 
    # --- Fim da verificação ---

    data = request.get_json()
    if not data: return jsonify({'erro': 'Requisição sem JSON'}), 400
         
    mensagem_usuario = data.get('mensagem') 
    user_id = data.get('user_id') 

    if not mensagem_usuario: return jsonify({'erro': 'Campo "mensagem" não fornecido'}), 400

    print(f"API /clara: Recebida msg de user_id: {user_id} - Msg: {mensagem_usuario}")

    try:
        resposta_clara = gerar_resposta_clara(mensagem_usuario, user_id) 
        try:
            timestamp = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute("INSERT INTO messages (sender, message, timestamp) VALUES (?, ?, ?)", ("Clara", resposta_clara, timestamp))
            conn.commit()
            conn.close()
        except Exception as db_err: print(f"Erro DB /clara: {db_err}")
        return jsonify({'resposta': resposta_clara}) 

    except Exception as e:
        print(f"Erro gerar_resposta_clara: {e}")
        return jsonify({'erro': 'Erro interno ao gerar resposta'}), 500

@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for('login')))
    resp.delete_cookie('token_clara') 
    print("Usuário deslogado.")
    return resp

# --- Execução do App ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000)) 
    # debug=False recomendado para produção e para evitar problemas com scheduler
    use_debug = os.environ.get("FLASK_DEBUG", "False") == "True"
    app.run(host='0.0.0.0', port=port, debug=use_debug)