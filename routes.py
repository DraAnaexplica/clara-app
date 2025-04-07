from flask import Flask, request, jsonify, render_template, redirect, url_for, make_response
import datetime
import sqlite3
import os
from openrouter_utils import gerar_resposta_clara

app = Flask(__name__)

# ========================
# CAMINHO ABSOLUTO DO BANCO
# ========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "tokens.db")

# ========================
# CRIAR BANCO DE TOKENS
# ========================
def criar_banco_tokens():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            descricao TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
            expira_em TEXT NOT NULL,
            ativo INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()

criar_banco_tokens()

# ========================
# VALIDAÇÃO DE TOKEN
# ========================
def validar_token(token):
    print("📍 tokens.db ABSOLUTO:", DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT expira_em, ativo FROM tokens WHERE token = ?", (token,))
    resultado = c.fetchone()
    conn.close()

    if resultado:
        expira_em_str, ativo = resultado
        if not ativo:
            return False
        expira_em = datetime.datetime.strptime(expira_em_str, "%Y-%m-%d").date()
        return expira_em >= datetime.date.today()
    return False

# ========================
# ROTAS DO USUÁRIO
# ========================
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        token = request.form.get("token", "")
        if validar_token(token):
            resp = make_response(redirect(url_for('index')))
            expira_em = datetime.datetime.now() + datetime.timedelta(days=30)
            resp.set_cookie("token_clara", token, expires=expira_em)
            return resp
        else:
            return render_template("login.html", erro="Token inválido ou expirado.")
    return render_template("login.html")

@app.route('/')
def index():
    token = request.cookies.get("token_clara")
    if not token or not validar_token(token):
        return redirect(url_for("login"))
    return render_template("index.html")

@app.route('/clara', methods=['POST'])
def conversar_com_clara():
    data = request.get_json()
    mensagem = data.get('mensagem')

    if not mensagem:
        return jsonify({'erro': 'Mensagem não fornecida'}), 400

    resposta = gerar_resposta_clara(mensagem)
    return jsonify({'resposta': resposta})

# ========================
# PAINEL DE CONTROLE
# ========================
@app.route('/painel', methods=["GET", "POST"])
def painel():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if request.method == "POST":
        descricao = request.form.get("descricao")
        expira_em = request.form.get("expira_em")
        token = request.form.get("novo_token")
        if token and expira_em:
            c.execute("""
                INSERT INTO tokens (token, expira_em, descricao, ativo)
                VALUES (?, ?, ?, 1)
            """, (token, expira_em, descricao))
            conn.commit()

    c.execute("SELECT token, expira_em, descricao FROM tokens ORDER BY expira_em")
    tokens = c.fetchall()
    conn.close()
    return render_template("painel.html", tokens=tokens)

@app.route('/atualizar_token', methods=["POST"])
def atualizar_token():
    token = request.form.get("token")
    nova_data = request.form.get("nova_data")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE tokens SET expira_em = ? WHERE token = ?", (nova_data, token))
    conn.commit()
    conn.close()
    return redirect("/painel")

@app.route('/excluir_token', methods=["POST"])
def excluir_token():
    token = request.form.get("token")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM tokens WHERE token = ?", (token,))
    conn.commit()
    conn.close()
    return redirect("/painel")

# ========================
# API EXTERNA PARA REGISTRAR TOKEN
# ========================
@app.route("/api/registrar_token", methods=["POST"])
def registrar_token():
    data = request.get_json()
    token = data.get("token")
    expira_em = data.get("expira_em")
    descricao = data.get("descricao", "")
    api_key = data.get("api_key")

    if api_key != os.getenv("TOKEN_API_KEY", ""):
        return jsonify({"erro": "Chave de API inválida"}), 403

    if not token or not expira_em:
        return jsonify({"erro": "Dados incompletos"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO tokens (token, expira_em, descricao, ativo)
            VALUES (?, ?, ?, 1)
        """, (token, expira_em, descricao))
        conn.commit()
        conn.close()
        return jsonify({"status": "salvo com sucesso"})
    except Exception as e:
        return jsonify({"erro": f"Erro ao salvar token: {str(e)}"}), 500

# ========================
# RODAR LOCALMENTE
# ========================
if __name__ == '__main__':
    app.run(debug=True)
