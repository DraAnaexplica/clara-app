import os
import logging
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv 
from openrouter_utils import gerar_resposta_clara, init_db # Importa funções necessárias

# --- Configuração Inicial ---

# Carrega variáveis de ambiente do arquivo .env (se existir)
# Essencial para desenvolvimento local. No Render, configure as vars no painel.
load_dotenv() 

# Configura logging básico 
# Em produção (Render), o Gunicorn pode lidar com logs, mas é bom ter um fallback.
log_level = logging.DEBUG if os.getenv("FLASK_DEBUG", "False").lower() == "true" else logging.INFO
logging.basicConfig(level=log_level, 
                    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# Cria a instância da aplicação Flask
app = Flask(__name__)

# Configura a chave secreta (importante para sessões, flash messages, etc.)
# Pega do .env ou usa um valor padrão (NÃO use o padrão em produção)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key-for-dev-only')
if app.config['SECRET_KEY'] == 'default-secret-key-for-dev-only' and not app.debug:
     app.logger.warning("ALERTA: Usando chave secreta padrão em ambiente de não-debug!")


# --- Inicialização do Banco de Dados ---

# Chama a inicialização do DB *antes* da primeira requisição à aplicação
@app.before_request
def initialize_database():
     # Usar app.before_request garante que roda antes de cada request,
     # mas podemos otimizar para rodar só uma vez.
     # No entanto, com SQLite, verificar a tabela antes de cada request é rápido.
     # Para garantir que a tabela exista mesmo se o app reiniciar.
     try:
         # A função init_db agora está em openrouter_utils.py
         init_db()
     except Exception as e:
         app.logger.critical(f"Falha CRÍTICA ao inicializar o banco de dados: {e}", exc_info=True)
         # Considerar retornar um erro 500 aqui se o DB for essencial.

# --- Rotas da Aplicação ---

@app.route("/", methods=["GET"])
def index():
    """Renderiza a página inicial do chat (interface HTML)."""
    app.logger.info(f"Renderizando index.html para {request.remote_addr}")
    # Nota: O histórico de chat NÃO é carregado aqui. O frontend (JS)
    # poderia opcionalmente fazer uma chamada para buscar o histórico inicial.
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat_endpoint():
    """Recebe a mensagem do usuário via POST JSON e retorna a resposta da Clara."""
    if not request.is_json:
        app.logger.warning(f"Requisição não JSON recebida em /chat de {request.remote_addr}")
        return jsonify({"error": "Requisição inválida. Corpo deve ser JSON."}), 415 # Unsupported Media Type

    data = request.get_json()
    
    mensagem_usuario = data.get("mensagem")
    # user_id é essencial para o histórico
    user_id = data.get("user_id") 

    # Validação de entrada
    if not mensagem_usuario or not isinstance(mensagem_usuario, str):
        app.logger.info(f"Mensagem inválida ou ausente em /chat para user_id='{user_id}'")
        return jsonify({"error": "O campo 'mensagem' é obrigatório e deve ser texto."}), 400
    if not user_id or not isinstance(user_id, str):
        app.logger.warning(f"Requisição em /chat sem 'user_id' válido de {request.remote_addr}")
        return jsonify({"error": "O campo 'user_id' é obrigatório e deve ser texto."}), 400
    if not mensagem_usuario.strip():
         app.logger.info(f"Mensagem vazia (apenas espaços) recebida de user_id='{user_id}'")
         return jsonify({"error": "A mensagem não pode consistir apenas de espaços."}), 400


    # Limitar tamanho da mensagem? (Opcional)
    MAX_MSG_LENGTH = 2000
    if len(mensagem_usuario) > MAX_MSG_LENGTH:
        app.logger.warning(f"Mensagem muito longa recebida de user_id='{user_id}'. Tamanho: {len(mensagem_usuario)}")
        return jsonify({"error": f"Mensagem excede o limite de {MAX_MSG_LENGTH} caracteres."}), 413 # Payload Too Large

    app.logger.info(f"Recebida mensagem de user_id='{user_id}'. Chamando gerar_resposta_clara...")

    try:
        # Chama a função principal que interage com a API e o DB
        resposta_clara = gerar_resposta_clara(mensagem_usuario, user_id)
        
        app.logger.info(f"Resposta gerada para user_id='{user_id}'. Enviando...")
        
        # Retorna a resposta da Clara em formato JSON
        return jsonify({"resposta": resposta_clara}), 200

    except Exception as e:
        # Captura qualquer erro inesperado na camada da aplicação Flask
        app.logger.critical(f"Erro inesperado na rota /chat para user_id='{user_id}': {e}", exc_info=True)
        # Retorna um erro genérico para o cliente
        return jsonify({"error": "Ocorreu um erro interno no servidor."}), 500

# Rota de health check (útil para o Render e outros serviços)
@app.route("/health", methods=["GET"])
def health_check():
     # Poderia adicionar verificações aqui (ex: testar conexão DB superficialmente)
     return jsonify({"status": "ok"}), 200

# --- Execução da Aplicação ---
if __name__ == "__main__":
    # app.run() é usado para desenvolvimento local. 
    # No Render, o Gunicorn será invocado (veja o Procfile).
    # host='0.0.0.0' permite acesso de outras máquinas na rede.
    # debug=True ativa recarregamento automático e mais detalhes de erro.
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    port = int(os.getenv("PORT", 5000)) # Render pode definir a PORT via env var
    
    app.logger.info(f"Iniciando Flask app em modo {'DEBUG' if debug_mode else 'PRODUÇÃO'} na porta {port}")
    # Desativa o reloader padrão do Flask se Gunicorn for usado, para evitar conflitos
    use_reloader = debug_mode 
    app.run(host="0.0.0.0", port=port, debug=debug_mode, use_reloader=use_reloader)