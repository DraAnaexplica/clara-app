import sqlite3
from datetime import datetime

# Conecta ao banco de dados que já existe
conn = sqlite3.connect("chat_history.db")
c = conn.cursor()

# Cria a tabela de tokens se não existir
c.execute("""
CREATE TABLE IF NOT EXISTS tokens (
    token TEXT PRIMARY KEY,
    expira_em TEXT
)
""")

# Insere um token de teste (opcional)
c.execute("INSERT OR IGNORE INTO tokens (token, expira_em) VALUES (?, ?)", ("teste123", "2025-04-30"))

conn.commit()
conn.close()
print("✅ Tabela criada e token de exemplo adicionado.")
