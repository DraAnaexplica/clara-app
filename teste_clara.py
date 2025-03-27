import requests
import json
import uuid

# URL da sua aplicação rodando no Render ou localmente
# url = "https://seu-app-name.onrender.com/" # Exemplo Render URL (POST na raiz '/')
url = "http://127.0.0.1:5000/" # URL Local (POST na raiz '/')

# Gera um ID de usuário único para este teste
test_user_id = str(uuid.uuid4()) 

# Mensagem a ser enviada
mensagem_data = {
    "mensagem": "Oi Clara, como está se sentindo hoje?",
    "user_id": test_user_id 
}

print(f"Enviando para: {url}")
print(f"Dados: {json.dumps(mensagem_data, indent=2)}")

try:
    # Faz a requisição POST para a rota raiz "/"
    resposta = requests.post(url, json=mensagem_data, timeout=30) 
    
    print(f"\nStatus Code: {resposta.status_code}")

    try:
        resposta_json = resposta.json()
        print("\nResposta JSON:")
        print(json.dumps(resposta_json, indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        print("\nResposta não é JSON válido:")
        print(resposta.text)

except requests.Timeout:
    print("\nErro: Timeout na requisição.")
except requests.exceptions.RequestException as e:
    print(f"\nErro ao fazer requisição: {e}")
except Exception as e:
    print(f"\nOcorreu um erro inesperado: {e}")


