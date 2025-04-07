import sqlite3

conn = sqlite3.connect("tokens.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT UNIQUE NOT NULL,
    descricao TEXT,
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
    expira_em TEXT NOT NULL,
    ativo INTEGER DEFAULT 1
)
""")

conn.commit()
conn.close()
print("✅ Tabela de tokens atualizada com nova estrutura.")

