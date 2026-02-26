import os
import shutil
import sys
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
            # Note que o id_banco é a primeira variável agora
            (id_banco, numero, dt_criacao, id_princ, ids_adicionais, acao, item, logradouro, bairro, status_conclusao, dt_conclusao, pasta, resp) = linha
            
            todos_ids = [id_princ] if id_princ else []
            if ids_adicionais and ids_adicionais != 'None':
                todos_ids.extend([i.strip() for i in ids_adicionais.split('-') if i.strip() != id_princ])
            
            status = status_conclusao or "NÃO"
            dias_aberto = "-"
            
            if dt_criacao:
                d_criacao = dt_criacao.date() if type(dt_criacao) is datetime else dt_criacao
                if status == "NÃO":
                    dias_aberto = f"{(datetime.now().date() - d_criacao).days} dias"
                elif status in ["SIM", "NÃO AUTORIZADA"] and dt_conclusao:
                    d_conclusao = dt_conclusao.date() if type(dt_conclusao) is datetime else dt_conclusao
                    dias_aberto = f"{(d_conclusao - d_criacao).days} dias"

            caminho_arquivo = self._reconstruir_caminho_os(pasta, numero, dt_criacao, todos_ids)
            acao_formatada = str(acao).upper() if acao else "-"
            item_formatado = str(item).upper() if item else "-"

            dados_formatados.append([
                id_banco, # 0 -> ID verdadeiro escondido
                numero, dt_criacao.strftime("%d/%m/%Y") if dt_criacao else "-",
                ", ".join(todos_ids), acao_formatada, item_formatado, bairro, status, 
                dias_aberto, pasta, resp, caminho_arquivo
            ])
        return dados_formatados

    def _formatar_dados_parecer(self, dados_brutos):
        dados_formatados = []
        for linha in dados_brutos:
            # O Parecer já salva o caminho completo no banco de dados, então não precisa reconstruir!
            (id_banco, num, tipo, proc, assun, ids, solic, dt_criacao, resp, caminho) = linha
            dt_str = dt_criacao.strftime("%d/%m/%Y") if dt_criacao else "-"
            dados_formatados.append([
                id_banco, # 0 -> ID verdadeiro escondido
                num, tipo, proc or "-", assun or "-", ids or "-", solic or "-", dt_str, resp or "-", caminho
            ])
        return dados_formatados

    # ---> NOVA LÓGICA DE ROTAS INTELIGENTES <---
    def _reconstruir_caminho_os(self, pasta, numero, dt_criacao, ids_list):
        if not pasta or pasta == "-": return None
        if not dt_criacao: return None
        
        mes, ano = dt_criacao.strftime("%m"), dt_criacao.strftime("%Y")
        
        # Puxa o ano que a OS foi criada e encaixa na nova árvore de diretórios do servidor
        if "URBMIDIA" in pasta.upper():
            base = rf"C:\Users\sousa\OneDrive\Documentos\ARQUIVOS SIGP - SIGA - SPR\SIGP\{ano}\ORDENS DE SERVICO\URBMIDIA"
        else:
            base = rf"C:\Users\sousa\OneDrive\Documentos\ARQUIVOS SIGP - SIGA - SPR\SIGP\{ano}\ORDENS DE SERVICO\PROXIMA PARADA"
            
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

    def buscar_detalhes_para_edicao(self, tipo_relatorio, id_banco):
        if tipo_relatorio == "OS": return self.repo.buscar_detalhes_os(id_banco)
        else: return self.repo.buscar_detalhes_parecer(id_banco)

    def salvar_edicao(self, tipo_relatorio, id_banco, dados_novos):
        if tipo_relatorio == "OS": return self.repo.atualizar_os(id_banco, dados_novos)
        else: return self.repo.atualizar_parecer(id_banco, dados_novos)

    def excluir_registro(self, tipo_relatorio, id_banco, motivo, usuario_logado):
        import json 
        
        if tipo_relatorio == "OS":
            dados_completos = self.repo.buscar_detalhes_os(id_banco)
            if not dados_completos: return False, "Não foi possível resgatar os dados para o Log."
            
            pasta_para_deletar = None
            dados_os = self.repo.obter_dados_para_caminho_os(id_banco)
            if dados_os:
                numero_real, dt_criacao, id_princ, ids_adicionais, pasta = dados_os
                todos_ids = [id_princ] if id_princ else []
                if ids_adicionais and ids_adicionais != 'None':
                    todos_ids.extend([i.strip() for i in ids_adicionais.split('-') if i.strip() != id_princ])
                caminho_arquivo = self._reconstruir_caminho_os(pasta, numero_real, dt_criacao, todos_ids)
                if caminho_arquivo: pasta_para_deletar = os.path.dirname(caminho_arquivo)
            
            sucesso, msg = self.repo.excluir_e_logar_os(id_banco, dados_completos, caminho_arquivo, motivo, usuario_logado)
            if sucesso and pasta_para_deletar and os.path.exists(pasta_para_deletar):
                try: shutil.rmtree(pasta_para_deletar)
                except: pass
            return sucesso, msg
            
        else: 
            dados_completos = self.repo.buscar_detalhes_parecer(id_banco)
            caminho_arquivo = self.repo.obter_caminho_parecer(id_banco)
            
            sucesso, msg = self.repo.excluir_e_logar_parecer(id_banco, dados_completos, caminho_arquivo, motivo, usuario_logado)
            if sucesso and caminho_arquivo and os.path.exists(caminho_arquivo):
                try: os.remove(caminho_arquivo)
                except: pass
            return sucesso, msg