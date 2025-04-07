import os
import requests
import sqlite3
from datetime import datetime
import pytz
from dotenv import load_dotenv
from prompt_builder import build_prompt
from memories import extrair_memoria, salvar_memorias, obter_memorias

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").replace('\n', '').replace('\r', '').strip()


def init_db():
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            user_id TEXT,
            sender TEXT,
            message TEXT,
            timestamp TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_memories (
            user_id TEXT,
            memoria TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_message(user_id, sender, message):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    timestamp = datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO messages (user_id, sender, message, timestamp) VALUES (?, ?, ?, ?)",
              (user_id, sender, message, timestamp))
    conn.commit()
    conn.close()


def get_history(user_id):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("SELECT sender, message FROM messages WHERE user_id = ? ORDER BY timestamp DESC LIMIT 5", (user_id,))
    history = c.fetchall()
    conn.close()
    return history


def detectar_estado(mensagem):
    mensagem = mensagem.lower()
    palavras_sexuais = [
        "gostosa", "delícia", "safada", "tesão", "tô com vontade",
        "me deixa louco", "gozar", "meter", "gemer", "gozo",
        "transar", "nua", "gozando", "vc me deixa doido", "com tesão"
    ]
    for palavra in palavras_sexuais:
        if palavra in mensagem:
            return "sexual"
    return "normal"


def gerar_resposta_clara(mensagem_usuario, user_id="local_user"):
    if not OPENROUTER_API_KEY:
        print("Erro: OPENROUTER_API_KEY não configurada!")
        return "⚠️ A Clara não conseguiu responder agora. Tenta mais tarde?"

    init_db()
    save_message(user_id, "Usuário", mensagem_usuario)

    # 🧠 Extração e salvamento de memórias
    novas_memorias = extrair_memoria(mensagem_usuario)
    if novas_memorias:
        print("🧠 Novas memórias detectadas:", novas_memorias)
        salvar_memorias(user_id, novas_memorias)

    # 🧠 Resposta direta baseada em memória
    msg_lower = mensagem_usuario.lower()
    perguntas_diretas = [
        "o que eu gosto",
        "qual meu",
        "você lembra do que eu gosto",
        "você lembra o que eu gosto",
        "lembra do que eu gosto"
    ]
    if any(p in msg_lower for p in perguntas_diretas):
        memorias = obter_memorias(user_id)
        if memorias:
            # Tenta buscar uma memória que fale de "gosto de"
            for mem in memorias:
                if "gosta de" in mem.lower() or "gosto de" in mem.lower():
                    resposta_direta = f"Claro que lembro, amor... você me disse que {mem.lower()} 😘"
                    save_message(user_id, "Clara", resposta_direta)
                    return resposta_direta
            # Se nenhuma for relevante, usa a última mesmo
            resposta_direta = f"Hmm... se eu não tô maluca, você me falou que {memorias[-1].lower()} 😏"
            save_message(user_id, "Clara", resposta_direta)
            return resposta_direta

    # Dados pra gerar o prompt dinâmico
    fuso_horario = pytz.timezone("America/Sao_Paulo")
    horario_atual = datetime.now(fuso_horario).strftime("%H:%M")

    historico = get_history(user_id)
    history_text = "\n".join([f"{s}: {m}" for s, m in reversed(historico)])

    nome_usuario = "André"
    estado = detectar_estado(mensagem_usuario)
    memorias = obter_memorias(user_id)

    prompt = build_prompt(nome_usuario, estado, memorias, historico=history_text, hora=horario_atual)

    mensagens_formatadas = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": mensagem_usuario}
    ]

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gryphe/mythomax-l2-13b",
        "messages": mensagens_formatadas
    }

    try:
        print("📤 Enviando prompt (estado:", estado, ")")
        print(prompt)
        response = requests.post(url, headers=headers, json=data, timeout=10)
        resposta = response.json()

        if "choices" in resposta and "message" in resposta["choices"][0]:
            reply = resposta["choices"][0]["message"]["content"]
            save_message(user_id, "Clara", reply)
            return reply
        else:
            print("⚠️ Estrutura inesperada na resposta:", resposta)
            return "⚠️ A Clara travou um pouco. Tenta de novo?"

    except Exception as e:
        print("❌ Erro ao processar resposta da Clara:", str(e))
        return "⚠️ A Clara teve um problema técnico. Tenta de novo?"


