import os
import psycopg2
from contextlib import contextmanager
from dotenv import load_dotenv

# Carrega o .env
load_dotenv()

# Configuração Centralizada
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "sistemas_etufor"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASS", "sua_senha"),
    "port": os.getenv("DB_PORT", "5432"),
}

@contextmanager
def get_db_connection():
    """
    Generator seguro de conexão.
    Uso:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM ...")
    
    Vantagem: Fecha a conexão automaticamente mesmo se der erro.
    """
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