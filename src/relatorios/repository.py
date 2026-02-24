import psycopg2
import json
from config.database import get_db_connection

class RelatorioRepository:
    # =========================================================
    # BUSCAS GERAIS (TABELA)
    # =========================================================
    def buscar_ordens_servico(self, filtros):
        # ATUALIZADO PARA AS COLUNAS NOVAS DO SIGP
        query = """
            SELECT numero, data_criacao, id_principal, ids_adicionais, 
                   acao_realizada, tipo_item, endereco, bairro, 
                   status_conclusao, data_conclusao, pasta_rede, responsavel
            FROM sigp.ordens_servico WHERE 1=1
        """
        params = []
        if filtros.get('id'):
            query += " AND (id_principal ILIKE %s OR ids_adicionais ILIKE %s)"
            params.extend([f"%{filtros['id']}%", f"%{filtros['id']}%"])
        if filtros.get('tipo_os') and filtros['tipo_os'] != "Todos":
            query += " AND acao_realizada ILIKE %s"
            params.append(f"%{filtros['tipo_os']}%")
        if filtros.get('tipo_item') and filtros['tipo_item'] != "Todos":
            query += " AND tipo_item ILIKE %s"
            params.append(f"%{filtros['tipo_item']}%")
        if filtros.get('bairro'):
            query += " AND bairro ILIKE %s"
            params.append(f"%{filtros['bairro']}%")
        if filtros.get('concluida') and filtros['concluida'] != "Todos":
            query += " AND status_conclusao = %s"
            params.append(filtros['concluida'])
        if filtros.get('pasta') and filtros['pasta'] != "Todos":
            query += " AND pasta_rede = %s"
            params.append(filtros['pasta'])
        if filtros.get('numero_os'):
            query += " AND numero = %s"
            params.append(int(filtros['numero_os']))
        if filtros.get('criado_por'):
            query += " AND responsavel ILIKE %s"
            params.append(f"%{filtros['criado_por']}%")
        if filtros.get('data_inicio') and filtros.get('data_fim'):
            query += " AND data_criacao BETWEEN %s AND %s"
            params.extend([filtros['data_inicio'], filtros['data_fim']])

        query += " ORDER BY data_criacao DESC"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    return cursor.fetchall()
        except Exception as e:
            print(f"Erro ao buscar OS: {e}") # Agora vai printar no terminal se der erro
            return []

    def buscar_pareceres(self, filtros):
        # ATUALIZADO PARA AS COLUNAS NOVAS DA TABELA FILHA E MÃE
        query = """
            SELECT b.numero_parecer_ano, p.tipo_parecer, p.processo, p.assunto, 
                   p.ids_associados, p.solicitante, b.created_at, u.nome_completo, p.caminho_arquivo
            FROM sigp.pareceres p
            JOIN common.pareceres_base b ON p.id = b.id
            LEFT JOIN common.usuarios u ON b.criado_por_id = u.id WHERE 1=1
        """
        params = []
        
        if filtros.get('solicitante') and filtros['solicitante'] != "Todos":
            query += " AND p.solicitante = %s"
            params.append(filtros['solicitante'])
        if filtros.get('assunto') and filtros['assunto'] != "Todos":
            query += " AND p.assunto = %s"
            params.append(filtros['assunto'])
            
        if filtros.get('processo'):
            query += " AND p.processo ILIKE %s"
            params.append(f"%{filtros['processo']}%")
        if filtros.get('numero_parecer'):
            query += " AND b.numero_parecer_ano = %s"
            params.append(int(filtros['numero_parecer']))
        if filtros.get('id'):
            query += " AND p.ids_associados ILIKE %s"
            params.append(f"%{filtros['id']}%")
        if filtros.get('tipo') and filtros['tipo'] != "Todos":
            query += " AND p.tipo_parecer = %s"
            params.append(filtros['tipo'].upper())
        if filtros.get('criado_por'):
            query += " AND u.nome_completo ILIKE %s"
            params.append(f"%{filtros['criado_por']}%")
        if filtros.get('data_inicio') and filtros.get('data_fim'):
            query += " AND DATE(b.created_at) BETWEEN %s AND %s"
            params.extend([filtros['data_inicio'], filtros['data_fim']])

        query += " ORDER BY b.created_at DESC"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    return cursor.fetchall()
        except Exception as e:
            print(f"Erro ao buscar Pareceres: {e}")
            return []

    # =========================================================
    # BUSCA DE TODOS OS DETALHES (POPUP)
    # =========================================================
    def buscar_detalhes_os(self, numero):
        query = """
            SELECT numero, TO_CHAR(data_criacao, 'DD/MM/YYYY'), id_principal, ids_adicionais, 
                   acao_realizada, tipo_item, endereco, bairro, complemento,
                   descricoes, responsavel, pasta_rede, status_conclusao
            FROM sigp.ordens_servico WHERE numero = %s
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (numero,))
                    row = cursor.fetchone()
                    if row:
                        colunas = ["Nº OS", "Data Criação", "ID Principal", "IDs Adicionais", 
                                   "Ação Realizada", "Tipo Item", "Endereço", "Bairro", "Complemento",
                                   "Descrição (Croqui)", "Criado por", "Modelo", "Status Conclusão"]
                        return dict(zip(colunas, row))
        except Exception as e:
            print(f"Erro Detalhes OS: {e}")
        return None

    def buscar_detalhes_parecer(self, numero):
        query = """
            SELECT b.numero_parecer_ano, TO_CHAR(b.created_at, 'DD/MM/YYYY'), p.tipo_parecer, 
                   p.processo, p.assunto, p.solicitante, p.ids_associados, p.tipo_execucao, 
                   p.item, p.endereco, p.quantidade, p.motivo_indeferimento, u.nome_completo
            FROM sigp.pareceres p
            JOIN common.pareceres_base b ON p.id = b.id
            LEFT JOIN common.usuarios u ON b.criado_por_id = u.id
            WHERE b.numero_parecer_ano = %s AND b.sistema_origem = 'SIGP'
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (numero,))
                    row = cursor.fetchone()
                    if row:
                        colunas = ["Nº Parecer", "Data Criação", "Decisão (DEFERIDO/INDEFERIDO)", "Processo", 
                                   "Assunto", "Solicitante", "IDs dos Pontos", "Ação Recomendada", 
                                   "Item", "Endereço", "Quantidade", "Motivo (Indeferido)", "Criado por"]
                        return dict(zip(colunas, row))
        except Exception as e:
            print(f"Erro Detalhes Parecer: {e}")
        return None

    # =========================================================
    # ATUALIZAÇÃO NO BANCO (COM MAIÚSCULAS)
    # =========================================================
    def atualizar_os(self, numero, dados):
        query = """
            UPDATE sigp.ordens_servico 
            SET id_principal=%s, ids_adicionais=%s, acao_realizada=%s, 
                tipo_item=%s, endereco=%s, bairro=%s, complemento=%s,
                descricoes=%s, status_conclusao=%s, 
                data_conclusao = CASE 
                    WHEN %s IN ('SIM', 'NÃO AUTORIZADA') THEN COALESCE(data_conclusao, CURRENT_TIMESTAMP)
                    ELSE NULL 
                END
            WHERE numero=%s
        """
        status = dados.get("Status Conclusão", "NÃO").strip().upper()
        acao_up = str(dados.get("Ação Realizada", "")).strip().upper()
        item_up = str(dados.get("Tipo Item", "")).strip().upper()
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (
                        dados.get("ID Principal"), dados.get("IDs Adicionais"), acao_up, 
                        item_up, dados.get("Endereço"), dados.get("Bairro"), 
                        dados.get("Complemento"), dados.get("Descrição (Croqui)"), status, status, numero
                    ))
            return True, "Ordem de Serviço atualizada com sucesso!"
        except Exception as e:
            return False, f"Erro ao atualizar: {e}"

    def atualizar_parecer(self, numero, dados):
        query = """
            UPDATE sigp.pareceres 
            SET tipo_parecer=%s, processo=%s, assunto=%s, solicitante=%s, 
                ids_associados=%s, tipo_execucao=%s, item=%s, endereco=%s,
                quantidade=%s, motivo_indeferimento=%s
            WHERE id = (SELECT id FROM common.pareceres_base WHERE numero_parecer_ano = %s AND sistema_origem = 'SIGP' LIMIT 1)
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (
                        dados.get("Decisão (DEFERIDO/INDEFERIDO)"), dados.get("Processo"), dados.get("Assunto"), 
                        dados.get("Solicitante"), dados.get("IDs dos Pontos"), dados.get("Ação Recomendada"), 
                        dados.get("Item"), dados.get("Endereço"), dados.get("Quantidade"), 
                        dados.get("Motivo (Indeferido)"), numero
                    ))
            return True, "Parecer atualizado com sucesso!"
        except Exception as e:
            return False, f"Erro ao atualizar: {e}"

    # =========================================================
    # DADOS PARA EXCLUSÃO DE ARQUIVOS E DELETAR DO BANCO
    # =========================================================
    def obter_dados_para_caminho_os(self, numero):
        query = "SELECT data_criacao, id_principal, ids_adicionais, pasta_rede FROM sigp.ordens_servico WHERE numero = %s"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (numero,))
                    return cur.fetchone()
        except: return None

    def obter_caminho_parecer(self, numero):
        query = """
            SELECT p.caminho_arquivo FROM sigp.pareceres p
            JOIN common.pareceres_base b ON p.id = b.id
            WHERE b.numero_parecer_ano = %s AND b.sistema_origem = 'SIGP'
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (numero,))
                    res = cur.fetchone()
                    return res[0] if res else None
        except: return None

    # =========================================================
    # EXCLUSÃO SEGURA COM LOG DE AUDITORIA (LIXEIRA)
    # =========================================================
    def excluir_e_logar_os(self, numero, dados_json, caminho_original, motivo, excluido_por):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO common.lixeira (modulo, numero, dados, caminho_original, motivo, excluido_por)
                        VALUES ('OS_SIGP', %s, %s, %s, %s, %s)
                    """, (numero, json.dumps(dados_json, ensure_ascii=False), caminho_original, motivo, excluido_por))
                    
                    cur.execute("DELETE FROM sigp.ordens_servico WHERE numero = %s", (numero,))
            return True, "OS excluída e registrada no Histórico com sucesso!"
        except Exception as e:
            return False, f"Erro no banco ao excluir: {e}"

    def excluir_e_logar_parecer(self, numero, dados_json, caminho_original, motivo, excluido_por):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM common.pareceres_base WHERE numero_parecer_ano = %s AND sistema_origem = 'SIGP' LIMIT 1", (numero,))
                    linha = cur.fetchone()
                    if not linha: return False, "Parecer não encontrado."
                    id_parecer = linha[0]

                    cur.execute("""
                        INSERT INTO common.lixeira (modulo, numero, dados, caminho_original, motivo, excluido_por)
                        VALUES ('PARECER_SIGP', %s, %s, %s, %s, %s)
                    """, (numero, json.dumps(dados_json, ensure_ascii=False), caminho_original, motivo, excluido_por))

                    cur.execute("DELETE FROM sigp.pareceres WHERE id = %s", (id_parecer,))
                    cur.execute("DELETE FROM common.pareceres_base WHERE id = %s", (id_parecer,))
                    
            return True, "Parecer excluído e registrado no Histórico com sucesso!"
        except Exception as e:
            return False, f"Erro no banco ao excluir: {e}"