import requests
import json
import uuid # Para gerar um user_id de teste
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente (se estiver testando localmente e tiver .env)
load_dotenv()

# --- Configuração ---
# Use a URL do Render ou a local
# BASE_URL = "https://seu-app-clara.onrender.com" # Exemplo Render URL
BASE_URL = os.getenv("TEST_BASE_URL", "http://127.0.0.1:5000") # Default para local
CHAT_ENDPOINT = "/chat" # Endpoint definido em app.py

# Gera um ID de usuário único para este teste específico
test_user_id = f"test-{uuid.uuid4()}" 

# Mensagem a ser enviada
mensagem_a_enviar = "Oi Clara, tudo bem por aí, meu bem? Como foi a sua tarde?"

# Dados a serem enviados no corpo da requisição (JSON)
payload = {
    "mensagem": mensagem_a_enviar,
    "user_id": test_user_id 
}

# --- Execução do Teste ---
url_completa = BASE_URL.rstrip('/') + CHAT_ENDPOINT

print(f"--- Testando Endpoint do Chat ---")
print(f"URL Target: {url_completa}")
print(f"User ID: {test_user_id}")
print(f"Mensagem: \"{mensagem_a_enviar}\"")
print("-" * 30)

try:
    # Faz a requisição POST com timeout
    resposta = requests.post(url_completa, json=payload, timeout=40) # Timeout um pouco maior que o da API
    
    print(f"Status Code: {resposta.status_code}")
    
    # Imprime headers importantes (opcional, útil para debug)
    print("Headers da Resposta:")
    print(f"  Content-Type: {resposta.headers.get('Content-Type')}")
    # print(f"  Date: {resposta.headers.get('Date')}")
    
    # Tenta decodificar a resposta como JSON
    try:
        resposta_json = resposta.json()
        print("\nResposta JSON Recebida:")
        # Usa json.dumps para formatar bem a saída
        print(json.dumps(resposta_json, indent=2, ensure_ascii=False)) 
        
        # Verifica se a chave 'resposta' existe (sucesso esperado)
        if 'resposta' in resposta_json:
             print("\n>>> Teste BEM SUCEDIDO (API retornou uma resposta) <<<")
        elif 'error' in resposta_json:
             print(f"\n>>> Teste FALHOU (API retornou um erro JSON: {resposta_json['error']}) <<<")
        else:
             print("\n>>> Teste INCONCLUSIVO (JSON recebido, mas sem 'resposta' ou 'error') <<<")

    except json.JSONDecodeError:
        # Se não for JSON, imprime o texto cru
        print("\nResposta NÃO é JSON válido:")
        print(resposta.text[:1000]) # Limita o output em caso de HTML de erro longo
        print("\n>>> Teste FALHOU (Resposta inesperada do servidor) <<<")

except requests.Timeout:
    print("\nErro: A requisição demorou muito (Timeout). O servidor pode estar lento ou inacessível.")
    print(">>> Teste FALHOU (Timeout) <<<")
except requests.ConnectionError:
     print(f"\nErro: Não foi possível conectar a {url_completa}. Verifique se o servidor está rodando e acessível.")
     print(">>> Teste FALHOU (Connection Error) <<<")
except requests.exceptions.RequestException as e:
    print(f"\nErro durante a requisição: {e}")
    print(">>> Teste FALHOU (Request Exception) <<<")
except Exception as e:
    print(f"\nOcorreu um erro inesperado no script de teste: {e}")
    print(">>> Teste FALHOU (Erro no Script) <<<")

print("-" * 30)



