from flask import Flask, request, jsonify, render_template, redirect, url_for, make_response
import datetime
from openrouter_utils import gerar_resposta_clara

app = Flask(__name__)

# Tokens válidos
TOKENS_VALIDOS = {
    "teste123": {"expira": "2025-04-30"},
    "vip456": {"expira": "2025-05-01"},
}

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        token = request.form.get("token", "")
        if token in TOKENS_VALIDOS:
            resp = make_response(redirect(url_for('index')))
            expira_em = datetime.datetime.now() + datetime.timedelta(days=30)
            resp.set_cookie("token_clara", token, expires=expira_em)
            return resp
        else:
            return render_template("login.html", erro="Token inválido.")
    return render_template("login.html")

@app.route('/')
def index():
    token = request.cookies.get("token_clara")
    if not token or token not in TOKENS_VALIDOS:
        return redirect(url_for("login"))
    return app.send_static_file('index.html')

@app.route('/clara', methods=['POST'])
def conversar_com_clara():
    data = request.get_json()
    mensagem = data.get('mensagem')

    if not mensagem:
        return jsonify({'erro': 'Mensagem não fornecida'}), 400

    resposta = gerar_resposta_clara(mensagem)
    return jsonify({'resposta': resposta})

if __name__ == '__main__':
    app.run(debug=True)
