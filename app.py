# --- INÍCIO DO ARQUIVO app.py (COM LOGS DE DEBUG INICIAIS) ---

import os
import sys  # Import sys para usar stderr
import logging
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
# Tenta importar as funções do outro arquivo, loga se falhar
try:
    from openrouter_utils import gerar_resposta_clara, init_db
    print("--- Funções de openrouter_utils importadas com sucesso ---", file=sys.stderr)
except ImportError as e:
    print(f"--- ERRO CRÍTICO: Falha ao importar de openrouter_utils: {e} ---", file=sys.stderr)
    # Se não conseguir importar, a app não vai funcionar, mas o log pode ajudar
    raise # Re-levanta o erro para parar a execução

# Log MUITO inicial para ver se o arquivo executa
print("--- app.py EXECUTANDO ---", file=sys.stderr)


# --- Configuração Inicial ---
# Chamada a load_dotenv() - tentará carregar .env se existir
try:
    load_dotenv()
    print("--- load_dotenv() chamado (tentativa) ---", file=sys.stderr)
except Exception as e:
    print(f"--- ERRO ao chamar load_dotenv(): {e} ---", file=sys.stderr)
    # Continuar mesmo se dotenv falhar, pois as vars podem vir do ambiente do Render

# Configura logging básico
# É importante fazer isso antes de criar o app Flask se quiser logar a criação
log_level_str = os.getenv("FLASK_DEBUG", "False").lower()
log_level = logging.DEBUG if log_level_str == "true" else logging.INFO
logging.basicConfig(level=log_level,
                    format='%(asctime)s %(levelname)s %(name)s:%(module)s:%(lineno)d: %(message)s', # Formato mais detalhado
                    datefmt='%Y-%m-%d %H:%M:%S')

print(f"--- Logging padrão configurado (Level: {log_level}) ---", file=sys.stderr)


# Cria a instância da aplicação Flask
try:
    app = Flask(__name__)
    print("--- Instância Flask criada ---", file=sys.stderr)

    # Configura a chave secreta
    secret_key_value = os.getenv('SECRET_KEY')
    if not secret_key_value:
        print("--- ALERTA: Variável de ambiente SECRET_KEY NÃO encontrada! Usando valor padrão inseguro. ---", file=sys.stderr)
        app.config['SECRET_KEY'] = 'default-secret-key-for-dev-only'
        if log_level != logging.DEBUG: # Avisa no logger padrão também se não estiver em debug
             logging.warning("ALERTA: Usando chave secreta padrão em ambiente de não-debug!")
    else:
        app.config['SECRET_KEY'] = secret_key_value
        print("--- SECRET_KEY carregada do ambiente ---", file=sys.stderr)

    # Verifica outra variável essencial
    if not os.getenv('OPENROUTER_API_KEY'):
         print("--- ALERTA: Variável de ambiente OPENROUTER_API_KEY NÃO encontrada! API não funcionará. ---", file=sys.stderr)
         logging.warning("Variável de ambiente OPENROUTER_API_KEY não definida.")
    else:
         print("--- OPENROUTER_API_KEY encontrada no ambiente ---", file=sys.stderr)

except Exception as e:
    print(f"--- ERRO CRÍTICO ao criar instância Flask ou definir config: {e} ---", file=sys.stderr)
    logging.critical(f"Erro ao inicializar Flask: {e}", exc_info=True) # Loga com mais detalhes
    raise # Re-levanta o erro para parar a execução e aparecer no log principal


# --- Inicialização do Banco de Dados ---
@app.before_request
def initialize_database():
     # Adicione um print similar dentro da função init_db em openrouter_utils.py também!
     # Ex: print("--- init_db() CHAMADA ---", file=sys.stderr)
     logging.debug("Chamando initialize_database() via before_request.")
     try:
         init_db()
         logging.debug("init_db() executado com sucesso.")
     except Exception as e:
         # Loga o erro mas TENTA continuar, pois nem toda rota precisa do DB talvez
         logging.critical(f"Falha ao inicializar o banco de dados via before_request: {e}", exc_info=True)
         # Considerar retornar um erro 503 Service Unavailable aqui?
         # return jsonify({"error": "Erro interno ao preparar banco de dados."}), 503


# --- Rotas da Aplicação ---

@app.route("/", methods=["GET"])
def index():
    """Renderiza a página inicial do chat (interface HTML)."""
    app.logger.info(f"Renderizando index.html para {request.remote_addr}")
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat_endpoint():
    """Recebe a mensagem do usuário via POST JSON e retorna a resposta da Clara."""
    app.logger.debug(f"Requisição recebida em /chat de {request.remote_addr}")
    if not request.is_json:
        app.logger.warning(f"Requisição não JSON recebida em /chat de {request.remote_addr}")
        return jsonify({"error": "Requisição inválida. Corpo deve ser JSON."}), 415

    data = request.get_json()
    if not data: # Checa se o JSON está vazio ou é inválido
         app.logger.warning(f"Corpo JSON vazio ou inválido recebido em /chat de {request.remote_addr}")
         return jsonify({"error": "Corpo JSON vazio ou inválido."}), 400

    mensagem_usuario = data.get("mensagem")
    user_id = data.get("user_id")

    # Validação de entrada aprimorada
    errors = {}
    if not mensagem_usuario or not isinstance(mensagem_usuario, str) or not mensagem_usuario.strip():
        errors['mensagem'] = "O campo 'mensagem' é obrigatório, deve ser texto e não pode ser vazio."
    if not user_id or not isinstance(user_id, str) or not user_id.strip():
        errors['user_id'] = "O campo 'user_id' é obrigatório e deve ser texto."

    # Limitar tamanho da mensagem
    MAX_MSG_LENGTH = 2000
    if isinstance(mensagem_usuario, str) and len(mensagem_usuario) > MAX_MSG_LENGTH:
        errors['mensagem'] = f"Mensagem excede o limite de {MAX_MSG_LENGTH} caracteres."

    if errors:
        app.logger.info(f"Requisição inválida em /chat de user_id='{user_id or 'N/A'}': {errors}")
        return jsonify({"error": "Dados inválidos.", "details": errors}), 400

    app.logger.info(f"Recebida mensagem válida de user_id='{user_id}'. Chamando gerar_resposta_clara...")

    try:
        # Chama a função principal que interage com a API e o DB
        resposta_clara = gerar_resposta_clara(mensagem_usuario, user_id)

        app.logger.info(f"Resposta gerada para user_id='{user_id}'. Enviando...")

        # Retorna a resposta da Clara em formato JSON
        return jsonify({"resposta": resposta_clara}), 200

    except Exception as e:
        # Captura qualquer erro inesperado na camada da aplicação Flask ou na lógica da API
        app.logger.critical(f"Erro inesperado processando /chat para user_id='{user_id}': {e}", exc_info=True)
        # Retorna um erro genérico para o cliente
        return jsonify({"error": "Ocorreu um erro interno inesperado no servidor."}), 500

# Rota de health check (útil para o Render e outros serviços)
@app.route("/health", methods=["GET"])
def health_check():
     # Verificação básica
     return jsonify({"status": "ok"}), 200

# --- Execução da Aplicação ---
# Este bloco só roda quando executamos 'python app.py' diretamente
if __name__ == "__main__":
    # Pega a porta do ambiente ou usa 5000 como padrão
    port = int(os.getenv("PORT", 5000))
    # Verifica o modo debug pelo ambiente
    is_debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    # O reloader automático do Flask só deve ser usado se NÃO estivermos rodando com Gunicorn
    # e estivermos em modo debug. Gunicorn gerencia seus próprios workers.
    use_reloader = is_debug_mode # Simplesmente ativa se estiver em debug local

    print(f"--- Bloco __main__ executando ---", file=sys.stderr)
    app.logger.info(f"Iniciando servidor de DESENVOLVIMENTO Flask em host=0.0.0.0 porta={port} debug={is_debug_mode}")
    # Nota: Em produção no Render, Gunicorn será usado via Procfile, este bloco não será o ponto de entrada principal.
    app.run(host="0.0.0.0", port=port, debug=is_debug_mode, use_reloader=use_reloader)

print("--- FIM DO ARQUIVO app.py ---", file=sys.stderr) # Log final

# --- FIM DO ARQUIVO app.py ---