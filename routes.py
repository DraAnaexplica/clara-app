def criar_banco_tokens():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Verifica se a coluna 'descricao' existe
    c.execute("PRAGMA table_info(tokens)")
    colunas = [col[1] for col in c.fetchall()]

    if 'descricao' not in colunas:
        print("📛 Estrutura antiga detectada. Recriando tabela tokens...")

        try:
            c.execute("ALTER TABLE tokens RENAME TO tokens_antigo")

            c.execute("""
                CREATE TABLE tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token TEXT UNIQUE NOT NULL,
                    descricao TEXT,
                    criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                    expira_em TEXT NOT NULL,
                    ativo INTEGER DEFAULT 1
                )
            """)

            c.execute("""
                INSERT INTO tokens (token, expira_em)
                SELECT token, expira_em FROM tokens_antigo
            """)

            c.execute("DROP TABLE tokens_antigo")
            conn.commit()
            print("✅ Tabela tokens atualizada com sucesso.")
        except Exception as e:
            print("❌ Erro ao migrar tabela:", e)
    else:
        print("✅ Tabela tokens já está atualizada.")

    conn.close()
