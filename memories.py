import sqlite3
import re

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
            memoria TEXT
        )
    """)
    for memoria in lista_memorias:
        c.execute("INSERT INTO user_memories (user_id, memoria) VALUES (?, ?)", (user_id, memoria))
    conn.commit()
    conn.close()


def obter_memorias(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT memoria FROM user_memories WHERE user_id = ?", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [m[0] for m in rows]
