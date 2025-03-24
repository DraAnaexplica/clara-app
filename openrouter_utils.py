import openai
import os
from claraprompt import prompt_clara
import os
print("🔍 VERIFICANDO CHAVE:", os.getenv("OPENAI_API_KEY"))

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = "https://openrouter.ai/api/v1"


def gerar_resposta_clara(mensagem_usuario):
    messages = [
        {"role": "system", "content": prompt_clara},
        {"role": "user", "content": mensagem_usuario}
    ]

    response = openai.ChatCompletion.create(
        model="anthropic/claude-3-haiku",
        messages=messages,
        temperature=0.85
    )

    print("RESPOSTA BRUTA:")
    print(response)

    # Protege caso não venha 'choices'
    if 'choices' not in response:
        return "⚠️ Erro ao gerar resposta da Clara. Verifique sua chave ou modelo."

    return response['choices'][0]['message']['content']


