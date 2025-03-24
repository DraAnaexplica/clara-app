from flask import Flask, request, jsonify
from openrouter_utils import gerar_resposta_clara

app = Flask(__name__)

@app.route('/clara', methods=['POST'])
def conversar_com_clara():
    data = request.get_json()
    mensagem = data.get('mensagem')
    user_id = data.get('user_id', 'default_user')  # Identificador do usuário

    if not mensagem:
        return jsonify({'erro': 'Mensagem não fornecida'}), 400

    resposta = gerar_resposta_clara(mensagem, user_id)
    return jsonify({'resposta': resposta})

if __name__ == '__main__':
    app.run(debug=True)