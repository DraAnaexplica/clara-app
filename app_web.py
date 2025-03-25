from flask import Flask, request, jsonify, render_template
from openrouter_utils import gerar_resposta_clara, save_message
from claraprompt import prompt_proactive

app = Flask(__name__)

# Inicializa o agendador automaticamente no deploy
def iniciar_agendador():
    try:
        import agendador  # Importa e ativa o agendador ao iniciar o app
    except Exception as e:
        print(f"[ERRO ao iniciar agendador] {e}")

iniciar_agendador()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Aceita tanto JSON quanto formulário
        if request.is_json:
            data = request.get_json()
            user_input = data.get("mensagem")
            user_id = data.get("user_id", request.remote_addr or "usuario-desconhecido")
        else:
            user_input = request.form.get("mensagem")
            user_id = request.remote_addr or "usuario-desconhecido"

        if not user_input:
            return jsonify({"erro": "Mensagem não fornecida"}), 400

        # Remove a dependência de prompt_inicial
        mensagem = f"Usuário: {user_input}"

        resposta = gerar_resposta_clara(mensagem, user_id=user_id)
        save_message(user_id, "Usuário", user_input)
        save_message(user_id, "Clara", resposta)
        return jsonify({"resposta": resposta})

    return render_template("index.html")

@app.route("/mensagens_novas", methods=["GET"])
def mensagens_novas():
    user_id = request.args.get("user_id", "usuario-desconhecido")
    mensagens = get_new_messages(user_id)
    return jsonify({"novas": mensagens})

if __name__ == "__main__":
    app.run(debug=True)
