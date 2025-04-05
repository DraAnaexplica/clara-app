from flask import Flask, request, jsonify, render_template, redirect, url_for, make_response
import datetime
import sqlite3
import uuid
from openrouter_utils import gerar_resposta_clara

app = Flask(__name__)

def criar_banco_tokens():
    conn = sqlite3.connect("tokens.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            token TEXT PRIMARY KEY,
            expira_em TEXT,
            user_id TEXT
        )
    """)
    conn.commit()
    conn.close()

criar_banco_tokens()

def validar_token(token, user_id=None):
    conn = sqlite3.connect("tokens.db")
    c = conn.cursor()
    if user_id:
        c.execute("SELECT expira_em FROM tokens WHERE token = ? AND user_id = ?", (token, user_id))
    else:
        c.execute("SELECT expira_em FROM tokens WHERE token = ?", (token,))
    resultado = c.fetchone()
    conn.close()
    if resultado:
        expira_em = datetime.datetime.strptime(resultado[0], "%Y-%m-%d").date()
        return expira_em >= datetime.date.today()
    return False

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        token = request.form.get("token", "")
        if validar_token(token):
            user_id = str(uuid.uuid4())
            expira_em = datetime.datetime.now() + datetime.timedelta(days=30)

            conn = sqlite3.connect("tokens.db")
            c = conn.cursor()
            c.execute("UPDATE tokens SET user_id = ? WHERE token = ?", (user_id, token))
            conn.commit()
            conn.close()

            resp = make_response(redirect(url_for('index')))
            resp.set_cookie("token_clara", token, expires=expira_em)
            resp.set_cookie("user_id", user_id, expires=expira_em)
            return resp
        else:
            return render_template("login.html", erro="Token inválido ou expirado.")
    return render_template("login.html")

@app.route('/')
def index():
    token = request.cookies.get("token_clara")
    user_id = request.cookies.get("user_id")
    if not token or not user_id or not validar_token(token, user_id):
        return redirect(url_for("login"))
    return render_template("index.html")

@app.route('/clara', methods=['POST'])
def conversar_com_clara():
    token = request.cookies.get("token_clara")
    user_id = request.cookies.get("user_id")
    if not token or not user_id or not validar_token(token, user_id):
        return jsonify({'erro': 'Acesso não autorizado'}), 403

    data = request.get_json()
    mensagem = data.get('mensagem')

    if not mensagem:
        return jsonify({'erro': 'Mensagem não fornecida'}), 400

    resposta = gerar_resposta_clara(mensagem, user_id=user_id)
    return jsonify({'resposta': resposta})

@app.route('/painel', methods=["GET", "POST"])
def painel():
    conn = sqlite3.connect("tokens.db")
    c = conn.cursor()
    if request.method == "POST":
        novo_token = request.form.get("novo_token")
        expira_em = request.form.get("expira_em")
        if novo_token and expira_em:
            c.execute("INSERT OR REPLACE INTO tokens (token, expira_em) VALUES (?, ?)", (novo_token, expira_em))
            conn.commit()

    c.execute("SELECT token, expira_em, user_id FROM tokens ORDER BY expira_em")
    tokens = c.fetchall()
    conn.close()
    return render_template("painel.html", tokens=tokens)

@app.route('/atualizar_token', methods=["POST"])
def atualizar_token():
    token = request.form.get("token")
    nova_data = request.form.get("nova_data")
    conn = sqlite3.connect("tokens.db")
    c = conn.cursor()
    c.execute("UPDATE tokens SET expira_em = ? WHERE token = ?", (nova_data, token))
    conn.commit()
    conn.close()
    return redirect("/painel")

@app.route('/excluir_token', methods=["POST"])
def excluir_token():
    token = request.form.get("token")
    conn = sqlite3.connect("tokens.db")
    c = conn.cursor()
    c.execute("DELETE FROM tokens WHERE token = ?", (token,))
    conn.commit()
    conn.close()
    return redirect("/painel")

if __name__ == '__main__':
    app.run(debug=True)
