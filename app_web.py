from flask import Flask, request, render_template, jsonify
from openrouter_utils import gerar_resposta_clara, save_message, get_new_messages
from agendador import scheduler
from claraprompt import prompt_inicial

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_message = request.form["message"]
        user_id = request.form["user_id"]

        # Gera resposta da Clara
        historico = []  # Ainda sem histórico real
        mensagem = f"{prompt_inicial}\n\nHistórico: {historico}\n\nUsuário: {user_message}"
        resposta = gerar_resposta_clara(mensagem)

        # Salva no banco
        save_message(user_id, "Usuário", user_message)
        save_message(user_id, "Clara", resposta)

        return render_template("index.html", resposta=resposta, user_id=user_id)

    return render_template("index.html", resposta=None, user_id="testuser")

@app.route("/mensagens_novas")
def mensagens_novas():
    user_id = request.args.get("user_id")
    mensagens = get_new_messages(user_id)
    return jsonify({"novas": mensagens})

if __name__ == "__main__":
    app.run(debug=True)

