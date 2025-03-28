import requests

url = "https://clara-app.onrender.com/clara"
data = {
    "mensagem": "Oi Clara, você tá online?",
    "user_id": "andre_render"
}

response = requests.post(url, json=data)

print("Status:", response.status_code)
print("Resposta da Clara:", response.json())
