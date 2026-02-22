import psycopg2
from config.database import get_db_connection
from datetime import datetime

class OSRepository:
    
    # --- MÉTODOS DE ENDEREÇO (SCHEMA COMMON) ---
    def buscar_endereco_por_id(self, id_procurado):
        query = """
            SELECT endereco, bairro, numero, complemento, status
            FROM common.enderecos WHERE id = %s
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (id_procurado,))
                    resultado = cursor.fetchone()
                    if resultado:
                        return {
                            "endereco": resultado[0],
                            "bairro": resultado[1],
                            "numero": resultado[2],
                            "complemento": resultado[3] or "",
                            "status": resultado[4] or "ATIVO"
                        }
            return None
        except Exception as e:
            print(f"[LOG DB] Erro ao buscar endereço: {e}")
            raise Exception(f"Erro ao buscar endereço no banco de dados.")

    def cadastrar_endereco(self, id_texto, endereco, numero, bairro, complemento, usuario):
        query = """
            INSERT INTO common.enderecos 
            (id, endereco, numero, bairro, complemento, status, ultima_vistoria_por, data_ultima_vistoria)
            VALUES (%s, %s, %s, %s, %s, 'ATIVO', %s, %s)
        """
        data_atual = datetime.now()
        params = (id_texto, endereco, numero, bairro, complemento, usuario, data_atual)
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
            return True
        except Exception as e:
            print(f"[LOG DB] Erro ao cadastrar endereço: {e}")
            raise Exception("Falha ao salvar o novo endereço no banco.")

    def atualizar_endereco(self, id_texto, endereco, numero, bairro, complemento, usuario, reativar=False):
        status = 'ATIVO' if reativar else None # Se não for reativar, mantém o que tá na query dinamicamente
        
        if reativar:
            query = """
                UPDATE common.enderecos
                SET endereco=%s, numero=%s, bairro=%s, complemento=%s, status='ATIVO',
                    ultima_vistoria_por=%s, data_ultima_vistoria=%s
                WHERE id=%s
            """
        else:
             query = """
                UPDATE common.enderecos
                SET endereco=%s, numero=%s, bairro=%s, complemento=%s,
                    ultima_vistoria_por=%s, data_ultima_vistoria=%s
                WHERE id=%s
            """
        
        data_atual = datetime.now()
        params = (endereco, numero, bairro, complemento, usuario, data_atual, id_texto)
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
            return True
        except Exception as e:
            print(f"[LOG DB] Erro ao atualizar endereço: {e}")
            raise Exception("Falha ao atualizar o endereço no banco.")

