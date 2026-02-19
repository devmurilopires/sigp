import os
import psycopg2
from contextlib import contextmanager
from dotenv import load_dotenv

# Carrega o .env obrigatoriamente
load_dotenv()

# Configuração Centralizada (Puxando APENAS do .env)
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "port": os.getenv("DB_PORT"),
}

@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        yield conn
        conn.commit()  # Confirma transação se não houver erro
    except Exception as e:
        if conn:
            conn.rollback()  # Desfaz se der erro
        raise e  # Relança o erro para a tela tratar
    finally:
        if conn:
            conn.close() # Garante fechamento