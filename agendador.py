from apscheduler.schedulers.background import BackgroundScheduler
from openrouter_utils import gerar_resposta_clara, save_message
from claraprompt import prompt_proactive
import atexit
import datetime
import sqlite3
from datetime import timedelta

# Ativar ou desativar o agendador
ativar_agendador = True

# Simulação de um user_id padrão (pode ser personalizado depois)
USER_ID = "user-automatico"

# Verifica se a última mensagem da Clara foi enviada recentemente
def ultima_mensagem_foi_recente(user_id):
    try:
        conn = sqlite3.connect("chat_history.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp FROM mensagens 
            WHERE user_id = ? AND remetente = 'Clara'
            ORDER BY timestamp DESC LIMIT 1
        """, (user_id,))
        resultado = cursor.fetchone()
        conn.close()

        if resultado:
            ultima_data = datetime.datetime.strptime(resultado[0], "%Y-%m-%d %H:%M:%S")
            agora = datetime.datetime.now()
            return (agora - ultima_data) < timedelta(minutes=4)  # só envia se passaram mais de 4 min
        return False
    except Exception as e:
        print(f"[Agendador] Erro ao verificar última mensagem: {e}")
        return False

# Função que será chamada automaticamente
def enviar_mensagem_automatica():
    if ultima_mensagem_foi_recente(USER_ID):
        print(f"[Agendador] Mensagem recente já enviada para {USER_ID}. Pulando envio.")
        return

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

