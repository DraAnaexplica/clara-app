from flask import Flask, render_template, request, jsonify
from openrouter_utils import gerar_resposta_clara

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = request.get_json()
        mensagem = data.get("mensagem", "")

        if not mensagem:
            return jsonify({"resposta": "⚠️ Nenhuma mensagem recebida."})

        resposta = gerar_resposta_clara(mensagem)
        return jsonify({"resposta": resposta})

    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
