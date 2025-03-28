from flask import Flask, request, jsonify, render_template
from gemini_utils import gerar_resposta_clara_gemini

app = Flask(__name__, static_folder='static', template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/clara', methods=['POST'])
def conversar_com_clara():
    data = request.get_json()
    mensagem = data.get('mensagem')
    user_id = data.get('user_id', '')  # garante memória por usuário

    if not mensagem:
        return jsonify({'erro': 'Mensagem não fornecida'}), 400

    resposta = gerar_resposta_clara_gemini(mensagem, user_id=user_id)
    return jsonify({'resposta': resposta})

if __name__ == '__main__':
    app.run(debug=True)
