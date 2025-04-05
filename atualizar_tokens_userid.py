# atualizar_tokens_userid.py
import sqlite3

conn = sqlite3.connect("tokens.db")
c = conn.cursor()

try:
    c.execute("ALTER TABLE tokens ADD COLUMN user_id TEXT")
    print("✅ Coluna user_id adicionada com sucesso.")
except sqlite3.OperationalError as e:
    print("⚠️ Parece que a coluna já existe ou houve um erro:", e)

conn.commit()
conn.close()
