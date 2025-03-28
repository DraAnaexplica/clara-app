# Lista de frases proibidas
BANNED_PHRASES = [
    "me conta", 
    "me diz", 
    "como você", 
    "o que você"
]

def validate(response: str) -> str:
    """Substitui perguntas por afirmações."""
    for phrase in BANNED_PHRASES:
        if phrase in response.lower():
            return response.replace("?", ".") + " 😈"
    return response