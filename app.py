# --- Conteúdo MINIMAL de app.py (para teste) ---
import os
import sys
from flask import Flask

print("--- MINIMAL app.py EXECUTANDO ---", file=sys.stderr)

try:
    app = Flask(__name__)
    print("--- MINIMAL Flask instance criada ---", file=sys.stderr)

    @app.route('/')
    def hello():
        print("--- MINIMAL Rota / acessada ---", file=sys.stderr)
        return "Hello from Minimal Render App!"

    # Adiciona rota health check básica também
    @app.route('/health')
    def health():
        print("--- MINIMAL Rota /health acessada ---", file=sys.stderr)
        return {"status": "ok"}

except Exception as e:
     print(f"--- ERRO CRÍTICO na criação MINIMAL: {e} ---", file=sys.stderr)
     raise

print("--- MINIMAL app.py carregado com sucesso ---", file=sys.stderr) 
# O bloco if __name__ == '__main__' não é usado por Gunicorn
# --- FIM do Conteúdo MINIMAL ---