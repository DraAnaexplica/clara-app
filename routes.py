from flask import Flask, request, jsonify, render_template, redirect, url_for, make_response
import datetime
import os
import psycopg2
from dotenv import load_dotenv
from datetime import date
from openrouter_utils import gerar_resposta_clara

load_dotenv()
app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL não definida!")

def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print(f"❌ Erro ao conectar ao PostgreSQL: {e}")
        return None

def criar_tabela_tokens_pg():
    conn = get_db_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tokens (
                    id SERIAL PRIMARY KEY,
                    token TEXT UNIQUE NOT NULL,
                    descricao TEXT,
                    criado_em TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    expira_em DATE NOT NULL,
                    ativo BOOLEAN DEFAULT TRUE
                );
            """)
            conn.commit()
            print("✅ Tabela 'tokens' criada/verificada.")
    except Exception as e:
        print(f"❌ Erro ao criar/verificar tabela: {e}")
        conn.rollback()
    finally:
        conn.close()

criar_tabela_tokens_pg()

def validar_token(token):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT expira_em, ativo FROM tokens WHERE token = %s", (token,))
            resultado = cur.fetchone()
    except Exception as e:
        print(f"❌ Erro ao validar token: {e}")
        return False
    finally:
        conn.close()
    if resultado:
        expira_em, ativo = resultado
        if not ativo:
            return False
        return expira_em >= datetime.date.today()
    return False

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

@app.route('/painel', methods=["GET", "POST"])
def painel():
    conn = get_db_connection()
    if not conn:
        return "Erro ao conectar ao banco de dados", 500
    try:
        if request.method == "POST":
            descricao = request.form.get("descricao")
            expira_em = request.form.get("expira_em")
            token = request.form.get("novo_token")
            if token and expira_em:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO tokens (token, expira_em, descricao, ativo)
                        VALUES (%s, %s, %s, TRUE)
                    """, (token, expira_em, descricao))
                    conn.commit()
        with conn.cursor() as cur:
            cur.execute("SELECT token, expira_em, descricao FROM tokens ORDER BY expira_em")
            tokens = cur.fetchall()
    except Exception as e:
        print(f"❌ Erro ao acessar painel: {e}")
        return "Erro ao acessar painel", 500
    finally:
        conn.close()
    print("📋 Tokens no painel:", tokens)
    return render_template("painel.html", tokens=tokens, now=date.today())

@app.route('/atualizar_token', methods=["POST"])
def atualizar_token():
    token = request.form.get("token")
    nova_data = request.form.get("nova_data")
    conn = get_db_connection()
    if not conn:
        return redirect("/painel")
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE tokens SET expira_em = %s WHERE token = %s", (nova_data, token))
            conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao atualizar token: {e}")
    finally:
        conn.close()
    return redirect("/painel")

@app.route('/excluir_token', methods=["POST"])
def excluir_token():
    token = request.form.get("token")
    conn = get_db_connection()
    if not conn:
        return redirect("/painel")
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tokens WHERE token = %s", (token,))
            conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao excluir token: {e}")
    finally:
        conn.close()
    return redirect("/painel")

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
    conn = get_db_connection()
    if not conn:
        return jsonify({"erro": "Erro ao conectar ao banco"}), 500
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO tokens (token, expira_em, descricao, ativo)
                VALUES (%s, %s, %s, TRUE)
            """, (token, expira_em, descricao))
            conn.commit()
            print(f"✅ Token salvo via API: {token}")
            return jsonify({"status": "salvo com sucesso"})
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return jsonify({"erro": "Este token já existe."}), 409
    except Exception as e:
        conn.rollback()
        print("❌ Erro ao salvar token:", e)
        return jsonify({"erro": f"Erro inesperado: {str(e)}"}), 500
    finally:
        conn.close()


