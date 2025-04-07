import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()  # Carrega as variáveis do .env

try:
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT"),
        dbname=os.getenv("PG_DBNAME"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD")
    )
    print("✅ Conexão bem-sucedida com o PostgreSQL!")
    conn.close()
except Exception as e:
    print("❌ Erro na conexão:")
    print(e)
