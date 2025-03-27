# --- Conteúdo esperado de app.py ---
import os
import logging
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv 
from openrouter_utils import gerar_resposta_clara, init_db 

load_dotenv() 

log_level = logging.DEBUG if os.getenv("FLASK_DEBUG", "False").lower() == "true" else logging.INFO
logging.basicConfig(level=log_level, 
                    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key-for-dev-only')
if app.config['SECRET_KEY'] == 'default-secret-key-for-dev-only' and not app.debug:
     app.logger.warning("ALERTA: Usando chave secreta padrão em ambiente de não-debug!")

@app.before_request
def initialize_database():
     try:
         init_db()
     except Exception as e:
         app.logger.critical(f"Falha CRÍTICA ao inicializar o banco de dados: {e}", exc_info=True)

@app.route("/", methods=["GET"])
def index():
    app.logger.info(f"Renderizando index.html para {request.remote_addr}")
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat_endpoint():
    # ... (resto do código da rota /chat) ...
    if not request.is_json:
        # ... (código de erro) ...
        return jsonify({"error": "Requisição inválida. Corpo deve ser JSON."}), 415

    data = request.get_json()
    mensagem_usuario = data.get("mensagem")
    user_id = data.get("user_id") 

    # ... (validações de mensagem_usuario e user_id) ...
    
    app.logger.info(f"Recebida mensagem de user_id='{user_id}'. Chamando gerar_resposta_clara...")
    try:
        resposta_clara = gerar_resposta_clara(mensagem_usuario, user_id)
        app.logger.info(f"Resposta gerada para user_id='{user_id}'. Enviando...")
        return jsonify({"resposta": resposta_clara}), 200
    except Exception as e:
        app.logger.critical(f"Erro inesperado na rota /chat para user_id='{user_id}': {e}", exc_info=True)
        return jsonify({"error": "Ocorreu um erro interno no servidor."}), 500

@app.route("/health", methods=["GET"])
def health_check():
     return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    port = int(os.getenv("PORT", 5000)) 
    app.logger.info(f"Iniciando Flask app em modo {'DEBUG' if debug_mode else 'PRODUÇÃO'} na porta {port}")
    use_reloader = debug_mode 
    app.run(host="0.0.0.0", port=port, debug=debug_mode, use_reloader=use_reloader)
# --- Fim do conteúdo esperado de app.py ---