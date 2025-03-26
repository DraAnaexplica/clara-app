from flask import Flask, request, jsonify, render_template
from openrouter_utils import gerar_resposta_clara
import logging

app = Flask(__name__)

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        mensagem = data.get("mensagem", "").strip()
        
        if not mensagem:
            return jsonify({"erro": "Mensagem vazia"}), 400
            
        resposta = gerar_resposta_clara(mensagem)
        return jsonify({"resposta": resposta})
        
    except Exception as e:
        logger.error(f"Erro no endpoint /chat: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)