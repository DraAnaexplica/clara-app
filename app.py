import os
import sqlite3
import requests # Necessário para send_proactive_message
import json     # Necessário para send_proactive_message
from datetime import datetime, timedelta # Importa timedelta também
from flask import Flask, request, jsonify, render_template, redirect, url_for, make_response, session # Adiciona session se for usar no futuro
import pytz     # Necessário para send_proactive_message
import schedule # Necessário para run_scheduler
import time     # Necessário para run_scheduler
import threading # Necessário para run_scheduler

# --- Importações das suas lógicas ---
# Assumindo que estes arquivos existem e contêm as funções/variáveis
try:
    from claraprompt import prompt_proactive # Usado em send_proactive_message
    # prompt_clara não parece ser usado diretamente se gerar_resposta_clara é usado em /clara
except ImportError:
    print("AVISO: Arquivo claraprompt.py ou variável prompt_proactive não encontrado.")
    prompt_proactive = "Instrução proativa padrão." # Fallback

try:
    # Usado na rota /clara
    from openrouter_utils import gerar_resposta_clara 
except ImportError:
    print("ERRO CRÍTICO: Arquivo openrouter_utils.py ou função gerar_resposta_clara não encontrado.")
    # Definir uma função fallback ou parar a execução pode ser necessário aqui
    def gerar_resposta_clara(mensagem): return "Erro: Módulo de resposta não encontrado."

# --- Configuração do App Flask ---
app = Flask(__name__)
# É ALTAMENTE RECOMENDADO configurar uma SECRET_KEY para usar sessions ou cookies seguros
# app.secret_key = os.urandom(24) # Exemplo: Gere uma chave segura

# Tokens válidos (do segundo trecho)
# CONSIDERAR mover para um arquivo de configuração ou banco de dados no futuro
TOKENS_VALIDOS = {
    "teste123": {"expira": "2025-04-30"}, # Expiração não está sendo usada na validação atual
    "vip456": {"expira": "2025-05-01"},
    # Adicione outros tokens conforme necessário
}

# Configuração do fuso horário (GMT-3) - do primeiro trecho
tz = pytz.timezone('America/Sao_Paulo')

# --- Configuração do Banco de Dados --- (do primeiro trecho)
DATABASE = 'chat_history.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Cria a tabela apenas se ela não existir
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  sender TEXT NOT NULL,
                  message TEXT NOT NULL,
                  timestamp TEXT NOT NULL)''') # Adicionado NOT NULL para boas práticas
    conn.commit()
    conn.close()

# Garante que o DB seja inicializado quando o app iniciar
init_db() 

# --- Funções de Mensagem Proativa --- (do primeiro trecho)

# Função para obter o horário atual em GMT-3
def get_current_time_str():
    return datetime.now(tz).strftime('%H:%M')

# Função para enviar mensagem proativa
def send_proactive_message():
    # Adicionar verificação de API Key aqui também é bom
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("Erro: GEMINI_API_KEY não configurada para mensagem proativa.")
        return

    print(f"[{datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')}] Tentando enviar mensagem proativa...")
    
    history_text = "Nenhuma mensagem anterior."
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        # Pega histórico mais recente para contexto
        c.execute("SELECT sender, message FROM messages ORDER BY id DESC LIMIT 10") # Aumentado limite p/ contexto
        history = c.fetchall()[::-1] # Inverte para ordem cronológica
        conn.close()
        if history:
             history_text = "\n".join([f"{sender}: {msg}" for sender, msg in history])
    except Exception as e:
        print(f"Erro ao buscar histórico para msg proativa: {e}")
        # Continua mesmo sem histórico

    # Preparar o prompt para mensagem proativa
    current_time = get_current_time_str()
    full_prompt = f"Contexto da conversa recente (se houver):\n{history_text}\n\nConsiderando o horário atual {current_time} (GMT-3), {prompt_proactive}"

    # Enviar requisição para o Gemini API (diretamente, como no snippet 1)
    print("Enviando requisição proativa para Gemini API...")
    headers = { "Content-Type": "application/json" }
    data = { "contents": [{ "parts": [{ "text": full_prompt }] }] }
    
    try:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={gemini_api_key}",
            headers=headers,
            json=data,
            timeout=60 # Adiciona timeout
        )
        response.raise_for_status() # Levanta erro para status >= 400

        print("Resposta proativa do Gemini API:", response.json())
        # Adicionar verificação se 'candidates' existe e não está vazio
        candidates = response.json().get('candidates')
        if candidates and candidates[0].get('content', {}).get('parts'):
            clara_response = candidates[0]['content']['parts'][0]['text'].strip()
            
            # Salvar a mensagem proativa no banco de dados
            timestamp = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute("INSERT INTO messages (sender, message, timestamp) VALUES (?, ?, ?)",
                      ("Clara", clara_response, timestamp))
            conn.commit()
            conn.close()
            print(f"Mensagem proativa salva: {clara_response}")
        else:
             print("Resposta proativa do Gemini vazia ou mal formada.")

    except requests.exceptions.RequestException as e:
        print(f"Erro de rede/API ao enviar mensagem proativa: {e}")
    except Exception as e:
        print(f"Erro inesperado ao processar mensagem proativa: {e}")


# --- Agendador (Scheduler) --- (do primeiro trecho)

# Função para rodar o agendador em uma thread separada
def run_scheduler():
    print("Iniciando agendador de mensagens proativas...")
    # Agendar mensagens proativas (ajuste os horários conforme necessário)
    schedule.every().day.at("11:00", tz=tz).do(send_proactive_message) # Mensagem às 11:00 GMT-3
    schedule.every().day.at("17:30", tz=tz).do(send_proactive_message) # Exemplo: Mensagem às 17:30 GMT-3
    # Adicione mais horários se desejar

    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print(f"Erro no loop do agendador: {e}")
        time.sleep(60) # Verifica a cada minuto

# Iniciar o agendador SE NÃO estiver no modo debug de recarregamento do Flask
# para evitar iniciar múltiplos agendadores
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("Thread do agendador iniciada.")
else:
     print("Agendador não iniciado em modo de recarregamento.")


# --- Rotas Flask ---

@app.route('/login', methods=["GET", "POST"])
def login():
    # <<< Lógica de login mantida do segundo trecho >>>
    if request.method == "POST":
        token_digitado = request.form.get("token", "")
        if token_digitado in TOKENS_VALIDOS:
            # Login bem-sucedido
            resp = make_response(redirect(url_for('index'))) # Redireciona para a rota index
            # Define o cookie com validade (ex: 30 dias)
            expira_em = datetime.now(tz) + timedelta(days=30) 
            resp.set_cookie("token_clara", token_digitado, expires=expira_em, httponly=True, samesite='Lax') # Adiciona flags de segurança ao cookie
            print(f"Login bem-sucedido para token: {token_digitado}")
            return resp
        else:
            # Token inválido
            print(f"Tentativa de login com token inválido: {token_digitado}")
            return render_template("login.html", erro="Token inválido ou expirado.")
    # Método GET (apenas mostra a página de login)
    return render_template("login.html")

@app.route('/')
def index():
    # <<< CORRIGIDO: Adicionada verificação de login via cookie >>>
    token = request.cookies.get("token_clara")
    if not token or token not in TOKENS_VALIDOS:
        print("Usuário não autenticado ou token inválido, redirecionando para login.")
        return redirect(url_for("login"))
    
    # Usuário autenticado, renderiza a página principal
    # Não precisa carregar mensagens aqui se o JS as busca ou se o histórico não é necessário no carregamento inicial
    print(f"Usuário autenticado com token: {token}. Renderizando index.html.")
    return render_template("index.html")


@app.route('/clara', methods=['POST'])
def conversar_com_clara():
    # <<< ADICIONADO: Verificação de token para a API >>>
    token = request.cookies.get("token_clara")
    if not token or token not in TOKENS_VALIDOS:
        print(f"Acesso não autorizado à API /clara sem token válido.")
        return jsonify({'erro': 'Acesso não autorizado'}), 401 
    # --- Fim da verificação ---

    # Lógica mantida do segundo trecho (usando gerar_resposta_clara)
    data = request.get_json()
    if not data:
         return jsonify({'erro': 'Requisição sem JSON'}), 400
         
    mensagem_usuario = data.get('mensagem') # Mudado para corresponder ao JS final
    user_id = data.get('user_id') # Pega o user_id enviado pelo JS

    if not mensagem_usuario:
        return jsonify({'erro': 'Campo "mensagem" não fornecido no JSON'}), 400

    print(f"Recebida mensagem de user_id: {user_id} - Mensagem: {mensagem_usuario}")

    # Chama a função do openrouter_utils para obter a resposta
    try:
        # Passar user_id e histórico se a função precisar
        resposta_clara = gerar_resposta_clara(mensagem_usuario, user_id) # Adapte se precisar de mais parâmetros
        
        # Salvar a conversa no DB (opcional, mas recomendado aqui também)
        try:
            timestamp = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            # Salva msg do usuário (se não for salva pelo JS antes da chamada)
            # c.execute("INSERT INTO messages (sender, message, timestamp) VALUES (?, ?, ?)",
            #           (user_id or "User", mensagem_usuario, timestamp)) 
            # Salva msg da Clara
            c.execute("INSERT INTO messages (sender, message, timestamp) VALUES (?, ?, ?)",
                      ("Clara", resposta_clara, timestamp))
            conn.commit()
            conn.close()
        except Exception as db_err:
             print(f"Erro ao salvar mensagem da Clara no DB: {db_err}")

        return jsonify({'resposta': resposta_clara}) # Retorna a chave 'resposta' esperada pelo JS

    except Exception as e:
        print(f"Erro ao chamar gerar_resposta_clara: {e}")
        return jsonify({'erro': 'Erro interno ao gerar resposta'}), 500

# Rota para logout (exemplo, opcional)
@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for('login')))
    resp.delete_cookie('token_clara') # Remove o cookie
    print("Usuário deslogado.")
    return resp

# --- Execução do App ---
if __name__ == '__main__':
    # Considerar usar Gunicorn ou Waitress em produção em vez de app.run()
    # Porta pode ser definida por variável de ambiente no Render
    port = int(os.environ.get("PORT", 5000)) 
    # debug=False em produção! O agendador pode ter problemas com debug=True.
    app.run(host='0.0.0.0', port=port, debug=os.environ.get("FLASK_DEBUG", "False") == "True")