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

        resposta = gerar_resposta_clara(mensagem, user_id=user_id)
        return jsonify({"resposta": resposta})

    return render_template("index.html")


# ✅ NOVA ROTA para buscar mensagens automáticas no chat.js
@app.route("/mensagens_novas")
def mensagens_novas():
    user_id = request.args.get("user_id", "")
    if not user_id:
        return jsonify({"erro": "user_id não fornecido."}), 400

    try:
        import sqlite3
        conn = sqlite3.connect("chat_history.db")
        c = conn.cursor()
        c.execute("SELECT message FROM messages WHERE user_id=? AND sender='Clara' ORDER BY timestamp DESC LIMIT 3", (user_id,))
        novas = [row[0] for row in c.fetchall()]
        conn.close()
        return jsonify({"novas": novas})
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar mensagens: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

