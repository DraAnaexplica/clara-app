import os # Adicionado para pegar a porta do ambiente
from flask import Flask, render_template, request, jsonify
# Presume que openrouter_utils.py está correto como você enviou
from openrouter_utils import gerar_resposta_clara 

app = Flask(__name__)

# Rota única para GET (servir HTML) e POST (receber chat)
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Verifica se o corpo da requisição é JSON
        if not request.is_json:
             return jsonify({"error": "Requisição inválida. Corpo deve ser JSON."}), 415
             
        data = request.get_json()
        if not data:
             return jsonify({"error": "Corpo JSON vazio ou inválido."}), 400

        mensagem = data.get("mensagem")
        user_id = data.get("user_id") # Recebe o user_id

        # Validações básicas
        if not mensagem or not isinstance(mensagem, str) or not mensagem.strip():
            return jsonify({"error": "O campo 'mensagem' é obrigatório e não pode ser vazio."}), 400
        if not user_id or not isinstance(user_id, str) or not user_id.strip():
             return jsonify({"error": "O campo 'user_id' é obrigatório."}), 400

        # Chama a função para gerar resposta (do openrouter_utils.py)
        # Tratar erros que podem vir de gerar_resposta_clara seria ideal aqui,
        # mas mantendo o mais próximo do seu original por enquanto.
        try:
             resposta = gerar_resposta_clara(mensagem, user_id=user_id)
             return jsonify({"resposta": resposta})
        except Exception as e:
             # Logar o erro aqui seria importante em produção
             print(f"Erro ao chamar gerar_resposta_clara: {e}") # Log simples para debug
             return jsonify({"error": "Erro interno ao processar a mensagem."}), 500

    # Se for GET, renderiza o template
    return render_template("index.html")

# Bloco para rodar localmente (Gunicorn no Render não usa isso)
if __name__ == "__main__":
    # Pega a porta do ambiente OU usa 5000 como padrão (bom para Render também)
    port = int(os.environ.get("PORT", 5000)) 
    # Roda no host 0.0.0.0 para ser acessível externamente (necessário para Render)
    # debug=False é mais seguro para não expor o debugger, mesmo localmente às vezes
    app.run(host="0.0.0.0", port=port, debug=False) # Debug False por padrão