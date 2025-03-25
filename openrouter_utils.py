import os
import requests
from claraprompt import prompt_clara
from datetime import datetime
import pytz  # Biblioteca pra lidar com fuso horário

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def gerar_resposta_clara(mensagem_usuario):
    if not GEMINI_API_KEY:
        print("Erro: GEMINI_API_KEY não configurada!")
        return "⚠️ A Clara teve dificuldade em responder agora. Tenta de novo?"

    # Obtém o horário atual no fuso GMT-3
    fuso_horario = pytz.timezone("America/Sao_Paulo")  # GMT-3
    horario_atual = datetime.now(fuso_horario).strftime("%H:%M")

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "contents": [{
            "parts": [{
                "text": f"{prompt_clara}\nHorário atual: {horario_atual} (GMT-3)\nUsuário: {mensagem_usuario}"
            }]
        }]
    }

    try:
        print("Enviando requisição pro Gemini API...")
        response = requests.post(f"{url}?key={GEMINI_API_KEY}", headers=headers, json=data, timeout=5)
        print("Resposta do Gemini API:", response.status_code, response.text)
        resposta = response.json()

        reply = resposta["candidates"][0]["content"]["parts"][0]["text"]
        return reply
    except requests.Timeout:
        print("Erro: Timeout na requisição pro Gemini API")
        return "⚠️ A Clara tá demorando pra responder. Tenta de novo?"
    except Exception as e:
        print("Erro ao processar resposta do Gemini:", str(e), resposta if 'resposta' in locals() else "Sem resposta")
        return "⚠️ A Clara teve dificuldade em responder agora. Tenta de novo?"


