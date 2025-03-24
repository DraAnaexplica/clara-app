import os
import requests
from claraprompt import prompt_clara

API_KEY = os.getenv("OPENROUTER_API_KEY")

def gerar_resposta_clara(mensagem_usuario):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "anthropic/claude-3-haiku",
        "messages": [
            {"role": "system", "content": prompt_clara},
            {"role": "user", "content": mensagem_usuario}
        ],
        "temperature": 0.85
    }

    response = requests.post(url, headers=headers, json=data)
    resposta = response.json()

    print("📨 RESPOSTA BRUTA:", resposta)

    try:
        return resposta["choices"][0]["message"]["content"]
    except Exception:
        return "⚠️ A Clara teve dificuldade em responder agora. Tenta de novo?"



