import os
import requests
import sqlite3
import json # Para decodificar erros JSON
import sys # <<--- ADICIONADO PARA USAR sys.stderr
from claraprompt import prompt_clara
from datetime import datetime
import pytz
import logging # Usar logging padrão

# Configurar logger (pegará a configuração feita em app.py se importado depois)
logger = logging.getLogger(__name__)

# --- Configuração ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DEFAULT_MODEL = "deepseek/deepseek-chat-v3-0324:free"
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)
DB_NAME = "chat_history.db" # Nome do arquivo do banco de dados
TIMEZONE = pytz.timezone("America/Sao_Paulo")
HISTORY_LIMIT = 10 # Número de mensagens do histórico a serem enviadas para a API
API_TIMEOUT = 25 # Timeout para a chamada da API em segundos

# --- Funções do Banco de Dados ---

def _get_db_connection():
    """Retorna uma conexão com o banco de dados."""
    try:
        # Timeout na conexão DB pode ser útil se o DB estiver em um volume de rede lento (raro com SQLite)
        conn = sqlite3.connect(DB_NAME, timeout=10)
        conn.row_factory = sqlite3.Row
        # Habilitar Foreign Key support se usar relações futuras
        # conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Erro ao conectar ao banco de dados '{DB_NAME}': {e}", exc_info=True)
        # Retorna None ou levanta uma exceção mais específica dependendo da criticidade
        return None

def init_db():
    """Cria a tabela de mensagens e índices se não existirem."""
    # Log de depuração adicionado aqui
    print("--- init_db() CHAMADA ---", file=sys.stderr)
    conn = _get_db_connection()
    if conn is None:
        # Log já feito em _get_db_connection
        # Levantar uma exceção para sinalizar falha crítica na inicialização
        # Isso impedirá que o app tente rodar sem o DB essencial
        print("--- ERRO CRÍTICO em init_db(): Falha ao conectar ao DB. ---", file=sys.stderr)
        raise ConnectionError(f"Não foi possível conectar ao banco de dados {DB_NAME} para inicialização.")

    try:
        # Usar 'with conn:' garante commit/rollback e fechamento automático
        with conn:
            c = conn.cursor()
            # Criação da tabela (IF NOT EXISTS previne erro se já existir)
            c.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            # Criação do índice (IF NOT EXISTS previne erro)
            # Índice composto ajuda a buscar e ordenar o histórico rapidamente
            c.execute("CREATE INDEX IF NOT EXISTS idx_user_id_timestamp ON messages (user_id, timestamp)")
        # Se 'with conn' terminar sem exceção, o commit é automático
        logger.info(f"Banco de dados '{DB_NAME}' verificado/inicializado com sucesso.")
        print("--- init_db() concluída com sucesso ---", file=sys.stderr) # Log de sucesso
    except sqlite3.Error as e:
        logger.error(f"Erro durante inicialização/verificação da tabela no DB: {e}", exc_info=True)
        print(f"--- ERRO em init_db() durante execução SQL: {e} ---", file=sys.stderr) # Log de erro
        # Propagar o erro para que a camada superior (app.py) saiba que houve falha
        raise

def save_message(user_id, sender, message):
    """Salva uma mensagem no banco de dados."""
    timestamp = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
    conn = _get_db_connection()
    if conn is None:
        logger.error(f"Não foi possível salvar mensagem para user_id='{user_id}': Falha na conexão DB.")
        return False # Indica falha

    try:
        with conn:
            conn.cursor().execute(
                "INSERT INTO messages (user_id, sender, message, timestamp) VALUES (?, ?, ?, ?)",
                (user_id, sender, message, timestamp)
            )
        # Commit automático ao sair do 'with' sem erro
        logger.debug(f"Mensagem salva para user_id='{user_id}'")
        return True # Indica sucesso
    except sqlite3.Error as e:
        logger.error(f"Erro ao salvar mensagem no DB para user_id='{user_id}': {e}", exc_info=True)
        return False # Indica falha

def get_history(user_id):
    """Recupera as últimas N mensagens do histórico para um usuário."""
    conn = _get_db_connection()
    if conn is None:
        logger.error(f"Não foi possível buscar histórico para user_id='{user_id}': Falha na conexão DB.")
        return [] # Retorna lista vazia

    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sender, message FROM messages WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
                (user_id, HISTORY_LIMIT)
            )
            history = [dict(row) for row in cursor.fetchall()]
        logger.debug(f"Histórico recuperado para user_id='{user_id}', {len(history)} mensagens.")
        return history
    except sqlite3.Error as e:
        logger.error(f"Erro ao buscar histórico do DB para user_id='{user_id}': {e}", exc_info=True)
        return [] # Retorna lista vazia em caso de erro

# --- Interação com a API OpenRouter ---

def gerar_resposta_clara(mensagem_usuario, user_id):
    """Envia a mensagem do usuário e o histórico para o OpenRouter e retorna a resposta."""
    # Verifica a chave da API
    if not OPENROUTER_API_KEY:
        logger.critical("OPENROUTER_API_KEY não está configurada! A API não pode ser chamada.")
        # É importante não expor a falta da chave ao usuário final diretamente
        return "⚠️ Desculpe, estou com um problema técnico interno e não consigo responder agora."

    # User ID é essencial, validação feita em app.py, mas checa aqui por segurança
    if not user_id:
        logger.error("gerar_resposta_clara chamada sem user_id válido.")
        return "⚠️ Erro interno: Identificação do usuário ausente."

    # 1. Salvar mensagem do usuário
    if not save_message(user_id, "Usuário", mensagem_usuario):
         logger.warning(f"Não foi possível salvar a mensagem do usuário {user_id} no DB. Continuando...")
         # Considerar se isso deve impedir a continuação

    # 2. Preparar dados para a API
    horario_atual = datetime.now(TIMEZONE).strftime("%H:%M")
    mensagens_formatadas = [{"role": "system", "content": prompt_clara}]

    # Adicionar histórico
    historico = get_history(user_id)
    for msg_data in reversed(historico): # Inverte para ordem cronológica
         sender = msg_data.get('sender')
         message_text = msg_data.get('message')
         if sender and message_text:
             role = "user" if sender.lower() == "usuário" else "assistant"
             mensagens_formatadas.append({"role": role, "content": message_text})
         else:
             logger.warning(f"Mensagem no histórico inválida/vazia ignorada para user_id='{user_id}': {msg_data}")

    # Adicionar mensagem atual do usuário com contexto de horário
    mensagens_formatadas.append({
        "role": "user",
        "content": f"{mensagem_usuario}\n(Horário atual: {horario_atual} GMT-3)"
    })

    # 3. Configurar e fazer a chamada para a API
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        # Opcional: Adicionar headers recomendados pelo OpenRouter
        # "HTTP-Referer": os.getenv("APP_URL", ""), # Idealmente, a URL pública do seu app
        # "X-Title": "Clara AI Chat",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": mensagens_formatadas,
        # "temperature": 0.7, # Exemplo de parâmetro adicional
    }

    # 4. Processar a resposta da API
    api_response_text = None
    try:
        logger.info(f"Enviando requisição para OpenRouter (Modelo: {OPENROUTER_MODEL}) para user_id='{user_id}'...")
        response = requests.post(url, headers=headers, json=payload, timeout=API_TIMEOUT)
        response.raise_for_status() # Levanta erro para status >= 400

        api_response_text = response.text
        resposta_json = response.json()

        # Validação mais segura da estrutura da resposta
        if not isinstance(resposta_json, dict):
             raise ValueError("Resposta da API não é um dicionário JSON válido.")
        choices = resposta_json.get("choices")
        if not isinstance(choices, list) or not choices:
             # Logar a resposta completa se a estrutura estiver errada
             logger.error(f"Resposta da API sem 'choices' válidos para user_id='{user_id}'. Resposta: {api_response_text}")
             raise ValueError("Resposta da API não contém 'choices' válidos.")
        message_data = choices[0].get("message")
        if not isinstance(message_data, dict):
             logger.error(f"Primeira escolha na resposta da API sem 'message' válido para user_id='{user_id}'. Resposta: {api_response_text}")
             raise ValueError("Primeira escolha na resposta da API não contém 'message' válido.")
        reply = message_data.get("content")
        if not isinstance(reply, str):
             logger.error(f"Conteúdo ('content') da mensagem na resposta da API não é string para user_id='{user_id}'. Resposta: {api_response_text}")
             raise ValueError("Conteúdo ('content') da mensagem na resposta da API não é uma string.")

        reply = reply.strip()

        if not reply:
             logger.warning(f"API retornou resposta vazia (após strip) para user_id='{user_id}'.")
             return "Hmm... não sei o que dizer. 🤔"

        logger.info(f"Resposta recebida e processada da API para user_id='{user_id}'.")

        # Salvar resposta da Clara
        if not save_message(user_id, "Clara", reply):
             logger.warning(f"Não foi possível salvar a resposta da Clara para {user_id} no DB.")

        return reply

    # Tratamento de Erros Específicos
    except requests.Timeout:
        logger.warning(f"Timeout ({API_TIMEOUT}s) na requisição para OpenRouter para user_id='{user_id}'.")
        return "⏱️ Demorei um pouco demais para pensar... Pode tentar de novo, por favor?"
    except requests.exceptions.HTTPError as e:
         status_code = e.response.status_code
         response_content = e.response.text[:500]
         logger.error(f"Erro HTTP {status_code} da API OpenRouter para user_id='{user_id}': {e}. Resposta: {response_content}", exc_info=True)
         # Mensagens específicas para erros comuns
         if status_code == 401: return "⚠️ Problema de autenticação com a API. (Chave inválida?)"
         if status_code == 402: return "⚠️ Problema de pagamento/crédito com a API."
         if status_code == 429: return "⏳ Muitas requisições! Por favor, aguarde um pouco antes de tentar novamente."
         if status_code >= 500: return f"⚠️ O servidor da API parece estar com problemas ({status_code}). Tente mais tarde."
         return f"⚠️ Ocorreu um erro de comunicação com a API ({status_code})."
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de Conexão/Rede para OpenRouter para user_id='{user_id}': {e}", exc_info=True)
        return "⚠️ Falha na conexão. Verifique sua internet ou tente mais tarde."
    except (json.JSONDecodeError, ValueError) as e:
         logger.error(f"Erro ao processar/validar resposta JSON da API para user_id='{user_id}': {e}. Resposta recebida (parcial): {api_response_text[:500]}", exc_info=True)
         return "⚠️ Tive um problema para entender a resposta da API... Tenta de novo?"
    except Exception as e:
        logger.critical(f"Erro inesperado não tratado em gerar_resposta_clara para user_id='{user_id}': {e}", exc_info=True)
        return "💥 Oh não! Algo deu muito errado aqui dentro. Tente novamente, por favor."

# --- FIM DO ARQUIVO openrouter_utils.py ---
