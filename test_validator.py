from core.validation.response_validator import validate

# Teste 1: Frase com pergunta
resposta_ruim = "Me conta o que você quer?"
print("Antes:", resposta_ruim)
print("Depois:", validate(resposta_ruim))  # Deve adicionar "😈"

# Teste 2: Frase correta
resposta_boa = "Vou te mostrar como se faz..."
print("Validação:", validate(resposta_boa))  # Deve retornar igual