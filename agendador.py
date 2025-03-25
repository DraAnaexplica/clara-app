
from apscheduler.schedulers.background import BackgroundScheduler
from openrouter_utils import gerar_resposta_clara
from openrouter_utils import save_message
from claraprompt import prompt_proactive
import atexit
import datetime

# Ativar ou desativar o agendador
ativar_agendador = True

# Simulação de um user_id padrão (pode ser personalizado depois)
USER_ID = "user-automatico"

# Função que será chamada automaticamente
def enviar_mensagem_automatica():
    horario_atual = datetime.datetime.now().strftime("%H:%M")
    mensagem_inicial = f"Envie uma mensagem proativa considerando o horário atual: {horario_atual}."
    mensagem = f"{prompt_proactive}\n\nHorário atual: {horario_atual}\n\nHistórico da conversa: []\n\n{mensagem_inicial}"

    resposta = gerar_resposta_clara(mensagem)
    save_message(USER_ID, "Clara", resposta)
    print(f"[Agendador] Mensagem automática enviada por Clara às {horario_atual}: {resposta}")

# Inicializa o agendador
if ativar_agendador:
    scheduler = BackgroundScheduler()
    scheduler.add_job(enviar_mensagem_automatica, 'interval', minutes=5)
    scheduler.start()
    print("[Agendador] Ativado: mensagens automáticas serão enviadas a cada 5 minutos.")

    # Garante que o agendador pare ao encerrar o app
    atexit.register(lambda: scheduler.shutdown())
else:
    print("[Agendador] Desativado.")
