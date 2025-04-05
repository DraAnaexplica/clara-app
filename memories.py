import sqlite3
import re
from datetime import datetime, timedelta

DB_PATH = "chat_history.db"

def extrair_memoria(texto):
    texto = texto.lower()

    padroes = [
        (r"gosto de (.+?)[\.\n!]", "Ele gosta de {}"),
        (r"tenho (medo|vergonha|dificuldade) de (.+?)[\.\n!]", "Ele tem {} de {}"),
        (r"sou (.+?)[\.\n!]", "Ele é {}"),
        (r"sinto falta de (.+?)[\.\n!]", "Ele sente falta de {}"),
        (r"trabalho como (.+?)[\.\n!]", "Ele trabalha como {}")
    ]

    memorias_encontradas = []

    for padrao, template in padroes:
        resultado = re.search(padrao, texto)
        if resultado:
            partes = resultado.groups()
            memoria = template.format(*partes)
            memorias_encontradas.append(memoria.strip())

    return memorias_encontradas

def salvar_memorias(user_id, lista_memorias):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_memories (
            user_id TEXT,
            memoria TEXT,
            ultima_vez TEXT
        )
    """)
    for memoria in lista_memorias:
        # Evita salvar memória repetida
        c.execute("SELECT 1 FROM user_memories WHERE user_id = ? AND memoria = ?", (user_id, memoria))
        if not c.fetchone():
            agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO user_memories (user_id, memoria, ultima_vez) VALUES (?, ?, ?)", (user_id, memoria, agora))
    conn.commit()
    conn.close()

def obter_memorias(user_id, intervalo_minutos=15):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT memoria, ultima_vez FROM user_memories WHERE user_id = ?", (user_id,))
    linhas = c.fetchall()
    agora = datetime.now()
    memorias_validas = []

    for memoria, ultima_vez in linhas:
        if not ultima_vez:
            memorias_validas.append(memoria)
            continue
        try:
            ultima = datetime.strptime(ultima_vez, "%Y-%m-%d %H:%M:%S")
            if agora - ultima > timedelta(minutes=intervalo_minutos):
                memorias_validas.append(memoria)
        except:
            memorias_validas.append(memoria)

    # Atualiza ultima_vez das memórias retornadas
    agora_str = agora.strftime("%Y-%m-%d %H:%M:%S")
    for memoria in memorias_validas:
        c.execute("UPDATE user_memories SET ultima_vez = ? WHERE user_id = ? AND memoria = ?", (agora_str, user_id, memoria))

    conn.commit()
    conn.close()
    return memorias_validas
