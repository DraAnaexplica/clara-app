from flask import Flask, request, jsonify
from gemini_utils import gerar_resposta_clara_gemini

app = Flask(__name__)

@app.route('/clara', methods=['POST'])
def conversar_com_clara():
    data = request.get_json()
    mensagem = data.get('mensagem')
    user_id = data.get('user_id', '')  # <- garante compatibilidade com memória

    if not mensagem:
        return jsonify({'erro': 'Mensagem não fornecida'}), 400

    resposta = gerar_resposta_clara_gemini(mensagem, user_id=user_id)
    return jsonify({'resposta': resposta})

@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(debug=True)
