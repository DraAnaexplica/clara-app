import sqlite3

conn = sqlite3.connect("chat_history.db")
c = conn.cursor()

try:
    c.execute("ALTER TABLE user_memories ADD COLUMN ultima_vez TEXT")
    print("✅ Coluna 'ultima_vez' adicionada com sucesso.")
except sqlite3.OperationalError:
    print("⚠️ Coluna 'ultima_vez' já existe.")

conn.commit()
conn.close()
