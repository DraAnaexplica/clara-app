import os
import requests
import sqlite3
from claraprompt import prompt_clara
from datetime import datetime
import pytz

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ... (init_db, save_message, get_history permanecem iguais)

def gerar_resposta_clara(mensagem_usuario, user_id=""):
    if not OPENROUTER_API_KEY:
        print("Erro: OPENROUTER_API_KEY não configurada!")
        return "⚠️ A Clara teve dificuldade em responder agora. Tenta de novo?"

    # Inicializa o banco de dados (se ainda não foi inicializado)
    init_db()

    # Salva a mensagem do usuário no banco de dados
    if user_id:
        save_message(user_id, "user", mensagem_usuario)

    # Obtém o horário atual no fuso GMT-3
    fuso_horario = pytz.timezone("America/Sao_Paulo")
    horario_atual = datetime.now(fuso_horario).strftime("%H:%M")

    # Recupera o histórico de mensagens
    history = get_history(user_id) if user_id else []
    history_text = "\n".join([f"{sender}: {msg}" for sender, msg in reversed(history)])

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gryphe/mythomax-l2-13b:free",  # Alteração: modelo específico
        "messages": [
            {"role": "system", "content": prompt_clara},
            {"role": "user", "content": f"Histórico da conversa:\n{history_text}\nHorário atual: {horario_atual} (GMT-3)\nMensagem: {mensagem_usuario}"}
        ]
    }

    try:
        print("Enviando requisição pro OpenRouter API...")
        response = requests.post(url, headers=headers, json=data, timeout=5)
        print("Resposta do OpenRouter API:", response.status_code, response.text)
        resposta = response.json()

        reply = resposta["choices"][0]["message"]["content"]

        # Salva a resposta da Clara no banco de dados
        if user_id:
            save_message(user_id, "Clara", reply)

        return reply
    except requests.Timeout:
        print("Erro: Timeout na requisição pro OpenRouter API")
        return "⚠️ A Clara tá demorando pra responder. Tenta de novo?"
    except Exception as e:
        print("Erro ao processar resposta do OpenRouter:", str(e), resposta if 'resposta' in locals() else "Sem resposta")
        return "⚠️ A Clara teve dificuldade em responder agora. Tenta de novo?"
