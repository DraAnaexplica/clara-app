# token_backup_utils.py
import sqlite3
import json
import os

def exportar_tokens():
    try:
        conn = sqlite3.connect("tokens.db")
        c = conn.cursor()
        c.execute("SELECT token, expira_em FROM tokens")
        tokens = c.fetchall()
        conn.close()

        with open("tokens_backup.json", "w") as f:
            json.dump(tokens, f)
        return True
    except:
        return False

def importar_tokens():
    try:
        if not os.path.exists("tokens_backup.json"):
            return False
        with open("tokens_backup.json", "r") as f:
            tokens = json.load(f)

        conn = sqlite3.connect("tokens.db")
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS tokens (token TEXT PRIMARY KEY, expira_em TEXT)")
        for token, expira_em in tokens:
            c.execute("INSERT OR REPLACE INTO tokens (token, expira_em) VALUES (?, ?)", (token, expira_em))
        conn.commit()
        conn.close()
        return True
    except:
        return False
