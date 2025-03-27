import os
import requests
import sqlite3
from claraprompt import prompt_clara # Presume que claraprompt.py está correto
from datetime import datetime
import pytz

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def init_db():
    # CUIDADO: Chamar init_db() a cada request pode ser ineficiente.
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            user_id TEXT,
            sender TEXT,
            message TEXT,
            timestamp TEXT
        )
    """)
    # Adicionar índice aqui seria bom para performance
    # c.execute("CREATE INDEX IF NOT EXISTS idx_user_id_timestamp ON messages (user_id, timestamp)")
    conn.commit()
    conn.close()

def save_message(user_id, sender, message):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    timestamp = datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    try:
        c.execute("INSERT INTO messages (user_id, sender, message, timestamp) VALUES (?, ?, ?, ?)",
                  (user_id, sender, message, timestamp))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Erro DB (save): {e}") # Log simples
    finally:
        conn.close()

def get_history(user_id):
    conn = sqlite3.connect("chat_history.db")
    # Definir row_factory pode ser útil
    # conn.row_factory = sqlite3.Row
    c = conn.cursor()
    history = [] # Valor padrão
    try:
        # Limitar histórico
        c.execute("SELECT sender, message FROM messages WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10", (user_id,)) # Aumentado limite para 10
        history = c.fetchall()
    except sqlite3.Error as e:
         print(f"Erro DB (get): {e}") # Log simples
    finally:
        conn.close()
    return history

def gerar_resposta_clara(mensagem_usuario, user_id=""):
    if not OPENROUTER_API_KEY:
        print("Erro Crítico: OPENROUTER_API_KEY não configurada!")
        # Mensagem mais genérica para o usuário
        return "⚠️ Desculpe, não consigo responder agora devido a um problema interno."

    # Chamar init_db() aqui pode gerar muitas conexões/verificações
    # Seria melhor chamar uma vez no início da aplicação Flask
    init_db() 
    
    if user_id:
        save_message(user_id, "Usuário", mensagem_usuario)
    else:
        # Se user_id é obrigatório, deveria retornar erro aqui
        print("Aviso: user_id não fornecido para gerar_resposta_clara")
        # return "⚠️ Erro: Identificação do usuário ausente." # Considerar descomentar

    fuso_horario = pytz.timezone("America/Sao_Paulo")
    horario_atual = datetime.now(fuso_horario).strftime("%H:%M")

    mensagens_formatadas = [
        { "role": "system", "content": prompt_clara }
    ]

    if user_id:
        historico = get_history(user_id)
        for sender, msg in reversed(historico): # Processa do mais antigo para o mais novo
             if sender and msg: # Checa se não são vazios/None
                role = "user" if sender.lower() == "usuário" else "assistant"
                mensagens_formatadas.append({"role": role, "content": msg})

    # Adiciona mensagem atual
    mensagens_formatadas.append({
        "role": "user",
        "content": f"{mensagem_usuario}\n(Horário atual: {horario_atual} GMT-3)" # Adicionado GMT-3 para clareza
    })

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    data = {
        # Usar modelo padrão ou variável de ambiente
        "model": os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat-v3-0324:free"),
        "messages": mensagens_formatadas
    }

    try:
        print(f"Enviando requisição pro OpenRouter (User: {user_id})...")
        response = requests.post(url, headers=headers, json=data, timeout=25) # Timeout aumentado
        response.raise_for_status() # Verifica erros HTTP (4xx, 5xx)
        
        resposta_json = response.json()
        
        # Validação mínima da resposta
        if "choices" in resposta_json and len(resposta_json["choices"]) > 0:
            message_content = resposta_json["choices"][0].get("message", {}).get("content")
            if message_content and isinstance(message_content, str):
                reply = message_content.strip()
                if reply and user_id:
                    save_message(user_id, "Clara", reply)
                return reply or "..." # Retorna '...' se a resposta for vazia após strip
            else:
                 print(f"Erro: Resposta API com estrutura inválida (content): {resposta_json}")
                 return "⚠️ Tive um problema para entender a resposta..."
        else:
            print(f"Erro: Resposta API com estrutura inválida (choices): {resposta_json}")
            return "⚠️ Tive um problema para entender a resposta..."

    except requests.Timeout:
        print(f"Erro: Timeout na requisição pro OpenRouter (User: {user_id})")
        return "⏱️ Demorei demais para responder... Tenta de novo?"
    except requests.exceptions.HTTPError as e:
         print(f"Erro HTTP {e.response.status_code} da API: {e.response.text[:200]}")
         # Mensagens mais amigáveis baseadas no status seriam melhores
         return f"⚠️ Erro {e.response.status_code} ao comunicar com a IA."
    except requests.exceptions.RequestException as e:
         print(f"Erro de Conexão/Rede: {e}")
         return "⚠️ Falha na conexão com a IA."
    except Exception as e:
        # Captura outros erros (JSONDecodeError, etc.)
        print(f"Erro inesperado ao processar resposta da IA: {type(e).__name__} - {e}")
        # Em produção, evitar expor detalhes do erro
        return "⚠️ A Clara teve um problema técnico inesperado."