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

    # --- MÉTODOS DE ORDEM DE SERVIÇO (SCHEMA SIGP) ---
    def buscar_historico_os(self, id_procurado, limite=5):
        query = """
            SELECT numero_os, data, tipo_os, tipo_item, endereco, bairro, criado_por
            FROM sigp.ordens_servico
            WHERE id_texto = %s
            ORDER BY data DESC
            LIMIT %s
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (id_procurado, limite))
                    return cursor.fetchall()
        except Exception as e:
            print(f"[LOG DB] Erro ao buscar histórico: {e}")
            return []

    def obter_proximo_numero_os(self, pasta_final, ano_atual):
        query = """
            SELECT MAX(numero_os)
            FROM sigp.ordens_servico
            WHERE pasta_final = %s AND RIGHT(data, 4) = %s
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (pasta_final, ano_atual))
                    resultado = cursor.fetchone()
                    if resultado and resultado[0] is not None:
                        return resultado[0] + 1
                    return 1
        except Exception as e:
            print(f"[LOG DB] Erro ao gerar numeração da OS: {e}")
            return 1 # Fallback seguro

    def salvar_os(self, dados_os):
        query = """
            INSERT INTO sigp.ordens_servico (
                numero_os, data, id_texto, ids_texto,
                tipo_os, tipo_os_normalizado,
                tipo_item, tipo_item_normalizado,
                endereco, bairro, bairro_normalizado,
                complemento, descricao, criado_por, pasta_final
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, dados_os)
            return True
        except Exception as e:
            print(f"[LOG DB] Erro ao salvar OS final: {e}")
            raise Exception("Falha ao registrar a Ordem de Serviço no banco de dados.")