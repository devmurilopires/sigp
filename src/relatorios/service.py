import os
import shutil
import subprocess
from datetime import datetime
from src.relatorios.repository import RelatorioRepository

class RelatorioService:
    def __init__(self):
        self.repo = RelatorioRepository()

    def buscar_dados(self, tipo_relatorio, filtros):
        if tipo_relatorio == "OS":
            dados_brutos = self.repo.buscar_ordens_servico(filtros)
            return self._formatar_dados_os(dados_brutos)
        elif tipo_relatorio == "PARECER":
            dados_brutos = self.repo.buscar_pareceres(filtros)
            return self._formatar_dados_parecer(dados_brutos)
        return []

    def _formatar_dados_os(self, dados_brutos):
        dados_formatados = []
        for linha in dados_brutos:
            (numero, dt_criacao, id_princ, ids_adicionais, acao, item, logradouro, bairro, status_conclusao, dt_conclusao, pasta, resp) = linha
            
            todos_ids = [id_princ] if id_princ else []
            if ids_adicionais and ids_adicionais != 'None':
                todos_ids.extend([i.strip() for i in ids_adicionais.split('-') if i.strip() != id_princ])
            
            status = status_conclusao or "NÃO"
            dias_aberto = "-"
            
            # --- CORREÇÃO DE DATAS AQUI ---
            # Garante que o Python vai usar apenas a Data (ignorando a Hora do TIMESTAMP do banco)
            if dt_criacao:
                d_criacao = dt_criacao.date() if type(dt_criacao) is datetime else dt_criacao
                
                if status == "NÃO":
                    dias_aberto = f"{(datetime.now().date() - d_criacao).days} dias"
                elif status in ["SIM", "NÃO AUTORIZADA"] and dt_conclusao:
                    d_conclusao = dt_conclusao.date() if type(dt_conclusao) is datetime else dt_conclusao
                    dias_aberto = f"{(d_conclusao - d_criacao).days} dias"
            # ------------------------------

            caminho_arquivo = self._reconstruir_caminho_os(pasta, numero, dt_criacao, todos_ids)

            acao_formatada = str(acao).upper() if acao else "-"
            item_formatado = str(item).upper() if item else "-"

            dados_formatados.append([
                numero, dt_criacao.strftime("%d/%m/%Y") if dt_criacao else "-",
                ", ".join(todos_ids), acao_formatada, item_formatado, bairro, status, 
                dias_aberto, pasta, resp, caminho_arquivo
            ])
        return dados_formatados

    def _formatar_dados_parecer(self, dados_brutos):
        dados_formatados = []
        for linha in dados_brutos:
            (num, tipo, proc, assun, ids, solic, dt_criacao, resp, caminho) = linha
            dt_str = dt_criacao.strftime("%d/%m/%Y") if dt_criacao else "-"
            dados_formatados.append([num, tipo, proc or "-", assun or "-", ids or "-", solic or "-", dt_str, resp or "-", caminho])
        return dados_formatados

    def _reconstruir_caminho_os(self, pasta, numero, dt_criacao, ids_list):
        if not pasta or pasta == "-": return None
        base = r"C:\Users\sousa\OneDrive\Documentos\pastasTeste\OS Paradas\SIGP\2026\URBMÍDIA - SIGP" if "URBMIDIA" in pasta.upper() else r"C:\Users\sousa\OneDrive\Documentos\pastasTeste\OS Paradas\SIGP\2026\PROXIMA PARADA - SIGP"
        if not dt_criacao: return None
        mes, ano = dt_criacao.strftime("%m"), dt_criacao.strftime("%Y")
        str_ids = "-".join(ids_list) if ids_list else "EMERGENCIA"
        return os.path.join(base, f"{str(numero).zfill(3)}-{mes}-{ano}-ID{str_ids}", f"O.S {str(numero).zfill(3)}-{ano}-ID{str_ids}.docx")

    def abrir_arquivo(self, caminho):
        if not caminho or not os.path.exists(caminho):
            return False, f"Arquivo não encontrado no caminho:\n{caminho}"
        try:
            if os.name == "nt": os.startfile(caminho)
            else: subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", caminho])
            return True, "Aberto com sucesso"
        except Exception as e:
            return False, f"Erro ao abrir: {e}"

    def buscar_detalhes_para_edicao(self, tipo_relatorio, numero):
        if tipo_relatorio == "OS": return self.repo.buscar_detalhes_os(numero)
        else: return self.repo.buscar_detalhes_parecer(numero)

    def salvar_edicao(self, tipo_relatorio, numero, dados_novos):
        if tipo_relatorio == "OS": return self.repo.atualizar_os(numero, dados_novos)
        else: return self.repo.atualizar_parecer(numero, dados_novos)

    # =======================================================
    # EXCLUSÃO SEGURA (PRIMEIRO O BANCO, DEPOIS O ARQUIVO)
    # =======================================================

    def excluir_registro(self, tipo_relatorio, numero, motivo, usuario_logado):
        import json # Certifique-se de importar json no topo do arquivo!
        
        if tipo_relatorio == "OS":
            # 1. Coleta TUDO para o Log
            dados_completos = self.repo.buscar_detalhes_os(numero)
            if not dados_completos: return False, "Não foi possível resgatar os dados para o Log."
            
            # Pega o caminho
            pasta_para_deletar = None
            dados_os = self.repo.obter_dados_para_caminho_os(numero)
            if dados_os:
                dt_criacao, id_princ, ids_adicionais, pasta = dados_os
                todos_ids = [id_princ] if id_princ else []
                if ids_adicionais and ids_adicionais != 'None':
                    todos_ids.extend([i.strip() for i in ids_adicionais.split('-') if i.strip() != id_princ])
                caminho_arquivo = self._reconstruir_caminho_os(pasta, numero, dt_criacao, todos_ids)
                if caminho_arquivo: pasta_para_deletar = os.path.dirname(caminho_arquivo)
            
            # 2. Transação de Banco (Loga e Deleta)
            sucesso, msg = self.repo.excluir_e_logar_os(numero, dados_completos, caminho_arquivo, motivo, usuario_logado)
            
            # 3. Destruição Física Permanente
            if sucesso and pasta_para_deletar and os.path.exists(pasta_para_deletar):
                try: shutil.rmtree(pasta_para_deletar)
                except: pass
            return sucesso, msg
            
        else: 
            # 1. Coleta TUDO para o Log
            dados_completos = self.repo.buscar_detalhes_parecer(numero)
            caminho_arquivo = self.repo.obter_caminho_parecer(numero)
            
            # 2. Transação de Banco (Loga e Deleta)
            sucesso, msg = self.repo.excluir_e_logar_parecer(numero, dados_completos, caminho_arquivo, motivo, usuario_logado)
            
            # 3. Destruição Física Permanente
            if sucesso and caminho_arquivo and os.path.exists(caminho_arquivo):
                try: os.remove(caminho_arquivo)
                except: pass
            return sucesso, msg