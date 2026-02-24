import pandas as pd
from config.database import get_db_connection

class EnderecoRepository:
    def salvar_ou_atualizar(self, id_ponto, endereco, numero, bairro, complemento, status, criado_por):
        query = """
            INSERT INTO sigp.enderecos_pontos 
            (id_ponto, endereco, numero, bairro, complemento, status, criado_por, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (id_ponto) DO UPDATE SET
                endereco = EXCLUDED.endereco,
                numero = EXCLUDED.numero,
                bairro = EXCLUDED.bairro,
                complemento = EXCLUDED.complemento,
                status = EXCLUDED.status,
                criado_por = EXCLUDED.criado_por,
                updated_at = CURRENT_TIMESTAMP;
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (id_ponto, endereco, numero, bairro, complemento, status, criado_por))
                conn.commit()
            return True, "Endereço salvo/atualizado com sucesso!"
        except Exception as e:
            return False, f"Erro no banco de dados: {e}"

    def listar_todos(self):
        query = """
            SELECT id_ponto, endereco, numero, bairro, complemento, status, criado_por, updated_at
            FROM sigp.enderecos_pontos
            ORDER BY id_ponto
        """
        try:
            with get_db_connection() as conn:
                df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            print(f"Erro ao listar endereços: {e}")
            return pd.DataFrame()