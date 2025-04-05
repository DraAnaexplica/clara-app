import sqlite3
import json

DB_PATH = "tokens.db"

def exportar_tokens():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT token, expira_em FROM tokens")
    tokens = [{"token": row[0], "expira_em": row[1]} for row in c.fetchall()]
    conn.close()

    with open("tokens_backup.json", "w", encoding="utf-8") as f:
        json.dump(tokens, f, ensure_ascii=False, indent=2)
    return True

def importar_tokens():
    try:
        with open("tokens_backup.json", "r", encoding="utf-8") as f:
            tokens = json.load(f)
    except FileNotFoundError:
        return False

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS tokens (token TEXT PRIMARY KEY, expira_em TEXT)")
    for t in tokens:
        c.execute("INSERT OR REPLACE INTO tokens (token, expira_em) VALUES (?, ?)", (t["token"], t["expira_em"]))
    conn.commit()
    conn.close()
    return True
