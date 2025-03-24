import openai
from claraprompt import prompt_clara

# Configuração da API OpenRouter
openai.api_key = "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"
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


