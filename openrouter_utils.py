import os
import requests
import sqlite3
import json # Para decodificar erros JSON
from claraprompt import prompt_clara
from datetime import datetime
import pytz
import logging # Usar logging padrão

# Configurar logger
logger = logging.getLogger(__name__)

# --- Configuração ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# Use um modelo padrão ou pegue da variável de ambiente
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
        conn = sqlite3.connect(DB_NAME, timeout=10) # Timeout na conexão DB
        # Retorna linhas como dicionários (mais fácil de usar)
        conn.row_factory = sqlite3.Row 
        return conn
    except sqlite3.Error as e:
        logger.error(f"Erro ao conectar ao banco de dados '{DB_NAME}': {e}", exc_info=True)
        return None # Retorna None se a conexão falhar

def init_db():
    """Cria a tabela de mensagens se ela não existir."""
    conn = _get_db_connection()
    if conn is None:
        logger.error("Não foi possível inicializar o DB: Falha na conexão.")
        # Levantar uma exceção pode ser apropriado se o DB for essencial
        raise ConnectionError(f"Não foi possível conectar ao banco de dados {DB_NAME}") 

    try:
        with conn: # Use 'with' para garantir commit/rollback e fechamento
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            # Criar índice composto para otimizar a busca e ordenação do histórico
            c.execute("CREATE INDEX IF NOT EXISTS idx_user_id_timestamp ON messages (user_id, timestamp)")
        logger.info(f"Banco de dados '{DB_NAME}' verificado/inicializado com sucesso.")
    except sqlite3.Error as e:
        logger.error(f"Erro ao inicializar/verificar tabela no DB: {e}", exc_info=True)
        # Propagar o erro para que a camada superior saiba que houve falha
        raise 
    # 'with conn' já fecha a conexão, mesmo se houver erro

def save_message(user_id, sender, message):
    """Salva uma mensagem no banco de dados."""
    timestamp = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
    conn = _get_db_connection()
    if conn is None:
        logger.error("Não foi possível salvar mensagem: Falha na conexão DB.")
        return False # Indica falha

    try:
        with conn:
            conn.cursor().execute(
                "INSERT INTO messages (user_id, sender, message, timestamp) VALUES (?, ?, ?, ?)",
                (user_id, sender, message, timestamp)
            )
        logger.debug(f"Mensagem salva para user_id='{user_id}'")
        return True # Indica sucesso
    except sqlite3.Error as e:
        logger.error(f"Erro ao salvar mensagem no DB para user_id='{user_id}': {e}", exc_info=True)
        return False # Indica falha
    # 'with conn' já fecha a conexão

def get_history(user_id):
    """Recupera as últimas N mensagens do histórico para um usuário."""
    conn = _get_db_connection()
    if conn is None:
        logger.error("Não foi possível buscar histórico: Falha na conexão DB.")
        return [] # Retorna lista vazia

    try:
        with conn:
            cursor = conn.cursor()
            # Seleciona as colunas necessárias, ordena por timestamp DESC e limita
            cursor.execute(
                "SELECT sender, message FROM messages WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
                (user_id, HISTORY_LIMIT)
            )
            # Retorna como lista de dicts [{sender: '...', message: '...'}, ...]
            history = [dict(row) for row in cursor.fetchall()] 
        logger.debug(f"Histórico recuperado para user_id='{user_id}', {len(history)} mensagens.")
        return history
    except sqlite3.Error as e:
        logger.error(f"Erro ao buscar histórico do DB para user_id='{user_id}': {e}", exc_info=True)
        return [] # Retorna lista vazia em caso de erro
    # 'with conn' já fecha a conexão

# --- Interação com a API OpenRouter ---

def gerar_resposta_clara(mensagem_usuario, user_id):
    """Envia a mensagem do usuário e o histórico para o OpenRouter e retorna a resposta."""
    if not OPENROUTER_API_KEY:
        logger.critical("OPENROUTER_API_KEY não está configurada! A API não pode ser chamada.")
        return "⚠️ Desculpe, não consigo responder agora. (Erro de configuração)"

    # 1. Salvar mensagem do usuário (se houver user_id válido)
    if user_id:
        if not save_message(user_id, "Usuário", mensagem_usuario):
             # Se não conseguir salvar, log já foi feito, mas continua a execução
             logger.warning(f"Não foi possível salvar a mensagem do usuário {user_id} no DB.")
             # Considerar retornar um erro aqui se salvar for crítico
             pass 
    else:
        # Um user_id válido é essencial para esta lógica
        logger.error("gerar_resposta_clara chamada sem user_id.")
        return "⚠️ Erro interno: Identificação do usuário ausente."

    # 2. Preparar dados para a API
    horario_atual = datetime.now(TIMEZONE).strftime("%H:%M")
    
    # Mensagem do sistema com o prompt da Clara
    mensagens_formatadas = [
        {"role": "system", "content": prompt_clara}
    ]

    # Adicionar histórico (somente se user_id foi fornecido - o que deve ser sempre o caso aqui)
    historico = get_history(user_id)
    # O histórico vem do mais recente para o mais antigo, precisamos inverter para ordem cronológica
    for msg_data in reversed(historico):
         # Verifica se 'sender' e 'message' existem e não são None/vazios
         sender = msg_data.get('sender')
         message_text = msg_data.get('message')
         if sender and message_text: # Checa se ambos são truthy
             role = "user" if sender.lower() == "usuário" else "assistant"
             mensagens_formatadas.append({"role": role, "content": message_text})
         else:
             logger.warning(f"Mensagem no histórico inválida/vazia para user_id='{user_id}': {msg_data}")

    # Adicionar mensagem atual do usuário
    mensagens_formatadas.append({
        "role": "user",
        "content": f"{mensagem_usuario}\n(Horário atual: {horario_atual} GMT-3)" # Adiciona contexto de horário
    })

    # 3. Configurar e fazer a chamada para a API
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json", # Indica que esperamos JSON
        # Opcional: Adicionar headers recomendados pelo OpenRouter para identificação
        # "HTTP-Referer": os.getenv("YOUR_SITE_URL", ""), # URL do seu site/app
        # "X-Title": os.getenv("YOUR_APP_NAME", "ClaraChatApp"), # Nome do seu app
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": mensagens_formatadas,
        # Opcional: Adicionar outros parâmetros como temperature, max_tokens, etc.
        # "temperature": 0.75,
        # "max_tokens": 250,
    }

    # 4. Processar a resposta da API
    api_response_text = None # Para logging em caso de erro de JSON
    try:
        logger.info(f"Enviando requisição para OpenRouter (Modelo: {OPENROUTER_MODEL}) para user_id='{user_id}'...")
        # Log do payload pode ser útil para debug, mas cuidado com dados sensíveis se existirem
        # logger.debug(f"Payload API: {json.dumps(payload, indent=2)}") 
        
        response = requests.post(url, headers=headers, json=payload, timeout=API_TIMEOUT) 
        response.raise_for_status() # Levanta erro para status >= 400

        api_response_text = response.text # Guardar texto para debug se JSON falhar
        resposta_json = response.json()
        
        # Validar estrutura da resposta antes de acessar
        if not isinstance(resposta_json, dict):
             raise ValueError("Resposta da API não é um dicionário JSON válido.")

        choices = resposta_json.get("choices")
        if not isinstance(choices, list) or not choices:
             raise ValueError("Resposta da API não contém 'choices' válidos.")

        message_data = choices[0].get("message")
        if not isinstance(message_data, dict):
             raise ValueError("Primeira escolha na resposta da API não contém 'message' válido.")

        reply = message_data.get("content")
        if not isinstance(reply, str): # Checa se é string, permitindo string vazia
             raise ValueError("Conteúdo ('content') da mensagem na resposta da API não é uma string.")

        reply = reply.strip() # Remove espaços em branco extras

        if not reply: # Checa se a resposta não está vazia APÓS strip()
             logger.warning(f"API retornou resposta vazia para user_id='{user_id}'.")
             # Considerar retornar uma mensagem padrão ou tentar novamente?
             return "🤔 Hum... fiquei sem palavras agora."

        logger.info(f"Resposta recebida da API para user_id='{user_id}'.")
        
        # Salvar resposta da Clara
        if not save_message(user_id, "Clara", reply):
             logger.warning(f"Não foi possível salvar a resposta da Clara para {user_id} no DB.")
             # Continua mesmo se não salvar a resposta

        return reply

    except requests.Timeout:
        logger.warning(f"Timeout ({API_TIMEOUT}s) na requisição para OpenRouter para user_id='{user_id}'.")
        return "⏱️ Demorei demais para responder... Pode tentar de novo, por favor?"
    except requests.exceptions.HTTPError as e:
         # Erros específicos HTTP (4xx, 5xx)
         status_code = e.response.status_code
         response_content = e.response.text[:500] # Limita tamanho do log
         logger.error(f"Erro HTTP {status_code} da API OpenRouter para user_id='{user_id}': {e}. Resposta: {response_content}", exc_info=True)
         if status_code == 401:
              return "⚠️ Problema de autenticação com a API. (Verifique a chave no servidor)"
         elif status_code == 402: # Payment Required
              return "⚠️ Problema de pagamento ou crédito com a API."
         elif status_code == 429: # Rate Limit
              return "⏳ Calma! Estou recebendo muitas mensagens. Tente novamente em alguns instantes."
         elif status_code >= 500: # Erro no servidor da API
              return f"⚠️ Ocorreu um problema no servidor da API ({status_code}). Tente mais tarde."
         else: # Outros erros 4xx
              return f"⚠️ Ocorreu um erro ({status_code}) ao me comunicar... Tente mais tarde."
    except requests.exceptions.RequestException as e:
        # Outros erros de conexão/rede
        logger.error(f"Erro de Conexão/Requisição para OpenRouter para user_id='{user_id}': {e}", exc_info=True)
        return "⚠️ Parece que estou com problemas de conexão... Tenta mais tarde?"
    except (json.JSONDecodeError, ValueError) as e: # Erros ao processar JSON ou estrutura inesperada
         logger.error(f"Erro ao processar resposta JSON da API para user_id='{user_id}': {e}. Resposta recebida: {api_response_text[:500]}", exc_info=True)
         return "⚠️ Tive um problema para processar a resposta... Tenta de novo?"
    except Exception as e:
        # Captura qualquer outro erro inesperado
        logger.critical(f"Erro inesperado não tratado ao gerar resposta para user_id='{user_id}': {e}", exc_info=True)
        return "💥 Ops! Algo deu muito errado do meu lado. Por favor, tente novamente."
