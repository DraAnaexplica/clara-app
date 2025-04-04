from flask import Flask, render_template, request, redirect, url_for, make_response

app = Flask(__name__)
app.secret_key = 'chave-secreta'

TOKENS_VALIDOS = {"123456", "meutoken"}

@app.route("/")
def index():
    token = request.cookies.get("token_clara")
    if token not in TOKENS_VALIDOS:
        return redirect(url_for("login"))
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        token = request.form.get("token")
        if token in TOKENS_VALIDOS:
            resp = make_response(redirect(url_for("index")))
            resp.set_cookie("token_clara", token, max_age=3600)
            return resp
        return render_template("login.html", erro="Token inválido")
    return render_template("login.html")

@app.route("/logout")
def logout():
    resp = make_response(redirect(url_for("login")))
    resp.delete_cookie("token_clara")
    return resp

if __name__ == "__main__":
    app.run(debug=True)