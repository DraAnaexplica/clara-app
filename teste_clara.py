import requests
import json

url = "http://127.0.0.1:5000/clara"
mensagem = {
    "mensagem": "Oi Clara, senti saudade de você hoje.",
    "user_id": "andreteste1"  # Identificador único do usuário
}

try:
    resposta = requests.post(url, json=mensagem)
    print("Status:", resposta.status_code)
    print("Texto puro da resposta:")
    print(json.dumps(resposta.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print("Erro ao fazer requisição:", e)




