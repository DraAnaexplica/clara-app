from flask import Flask, render_template, request, jsonify
from openrouter_utils import gerar_resposta_clara
import agendador  # Ativa mensagens automáticas da Clara

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = request.get_json()
        mensagem = data.get("mensagem", "")
        user_id = data.get("user_id", "")  # Recebe o user_id

        if not mensagem:
            return jsonify({"resposta": "⚠️ Nenhuma mensagem recebida."})

        # Passa o user_id pro gerar_resposta_clara (ainda não será usado)
        resposta = gerar_resposta_clara(mensagem, user_id=user_id)
        return jsonify({"resposta": resposta})

    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

