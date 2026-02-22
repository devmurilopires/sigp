import os
import unicodedata
from datetime import datetime
from docx import Document
from docx.shared import Inches
from src.ordem_servico.repository import OSRepository

# Tenta puxar o utils, se não achar, cria um fallback local
try:
    from src.shared.utils import resource_path
except ImportError:
    def resource_path(path): return path

class OSService:
    def __init__(self):
        self.repo = OSRepository()

    def normalizar(self, texto: str) -> str:
        """Remove acentos e deixa em caixa alta."""
        if not texto: return ""
        nfkd = unicodedata.normalize('NFKD', texto)
        sem_acentos = "".join(c for c in nfkd if not unicodedata.combining(c))
        return sem_acentos.upper()

    def consultar_endereco(self, id_procurado):
        """Busca o endereço e retorna para a View."""
        return self.repo.buscar_endereco_por_id(id_procurado)

    def obter_historico_formatado(self, id_procurado):
        """Busca o histórico e formata em texto para o popup."""
        historico = self.repo.buscar_historico_os(id_procurado)
        if not historico:
            return "Nenhuma movimentação encontrada para este ID."
        
        texto = ""
        for r in historico:
            texto += f"OS: {r[0]} | Data: {r[1]} | Tipo: {r[2]} | Item: {r[3]}\nEndereço: {r[4]} - {r[5]} | Por: {r[6]}\n"
            texto += "-" * 50 + "\n"
        return texto

    def processar_criacao_os(self, descricoes_acumuladas, pasta_escolhida, modelo_escolhido, tipo_os, tipo_item, form_dados, usuario_logado):
        """Orquestra a criação: Atualiza Endereços -> Gera Word -> Salva no Banco."""
        
        if not descricoes_acumuladas:
            return False, "Adicione pelo menos uma descrição na tabela."

        # 1. Definição de Caminhos
        if pasta_escolhida == "URBMIDIA":
            pasta_base = r"\\172.20.0.57\dados\DIPLA\OS Paradas\SIGP\2026\URBMÍDIA - SIGP"
        else:
            pasta_base = r"\\172.20.0.57\dados\DIPLA\OS Paradas\SIGP\2026\PROXIMA PARADA - SIGP"

        if not os.path.exists(pasta_base):
            return False, f"A pasta de rede não está acessível:\n{pasta_base}"

        ids_unicos = list(set([d["id"] for d in descricoes_acumuladas]))
        ids_formatado = "-".join(ids_unicos)
        id_principal = descricoes_acumuladas[0]["id"]

        # 2. Atualização dos Endereços no Banco
        for id_atual in ids_unicos:
            dados_id = self.repo.buscar_endereco_por_id(id_atual)
            try:
                if not dados_id:
                    self.repo.cadastrar_endereco(id_atual, form_dados['endereco'], form_dados['numero'], form_dados['bairro'], form_dados['complemento'], usuario_logado)
                else:
                    reativar = dados_id["status"].strip().upper() == "INATIVO"
                    self.repo.atualizar_endereco(id_atual, form_dados['endereco'], form_dados['numero'], form_dados['bairro'], form_dados['complemento'], usuario_logado, reativar=reativar)
            except Exception as e:
                return False, str(e)

        # 3. Preparação para o Documento Word
        ano_atual = datetime.now().strftime('%Y')
        numero_os = self.repo.obter_proximo_numero_os(pasta_escolhida, ano_atual)
        data_str = datetime.now().strftime("%d/%m/%Y")

        # Tratamento de Strings para a OS
        endereco_completo = descricoes_acumuladas[0]["descricao"].split(" NA ")[-1].split(",")[0].strip()
        bairro_str = form_dados['bairro']
        complemento_str = form_dados['complemento']
        
        try:
            if "BAIRRO" in descricoes_acumuladas[0]["descricao"]:
                bairro_str = descricoes_acumuladas[0]["descricao"].split("BAIRRO")[-1].split(",")[0].strip()
            if "-" in bairro_str:
                partes = bairro_str.split("-", 1)
                bairro_str = partes[0].strip()
                complemento_str = partes[1].strip()
        except:
            pass # Mantém o que veio do form

        # 4. Geração do Arquivo Físico (.docx)
        nome_pasta = f"{numero_os:03d}-{datetime.now().strftime('%m')}-{ano_atual}-ID{'-'.join(ids_unicos) if ids_unicos else 'EMERGENCIA'}"
        caminho_pasta = os.path.join(pasta_base, nome_pasta)
        os.makedirs(caminho_pasta, exist_ok=True)

        nome_arquivo = f"O.S {numero_os:03d}-{ano_atual}-ID{'-'.join(ids_unicos) if ids_unicos else 'EMERGENCIA'}.docx"
        destino_docx = os.path.join(caminho_pasta, nome_arquivo)

        try:
            self._gerar_documento_modelo(resource_path(modelo_escolhido), destino_docx, numero_os, data_str, id_principal, descricoes_acumuladas)
        except Exception as e:
            return False, f"Erro ao gerar o arquivo Word:\n{e}"

        # 5. Salvar a OS final no Banco
        dados_salvar_os = (
            numero_os, data_str, id_principal, ids_formatado,
            tipo_os, self.normalizar(tipo_os),
            tipo_item, self.normalizar(tipo_item),
            endereco_completo, bairro_str, self.normalizar(bairro_str),
            complemento_str, "\n".join([item["descricao"] for item in descricoes_acumuladas]),
            usuario_logado, pasta_escolhida
        )

        try:
            self.repo.salvar_os(dados_salvar_os)
            return True, f"OS criada e salva com sucesso!\n{nome_arquivo}"
        except Exception as e:
            # Se deu erro no banco, o ideal seria apagar o arquivo docx gerado, mas vamos focar no aviso
            return False, str(e)


    # --- Função Interna para Manipular o Word ---
    def _gerar_documento_modelo(self, modelo_path, destino_path, numero_os, data_str, id_texto, descricoes):
        doc = Document(modelo_path)
        mapeamento = {
            "{{NUMERO_OS}}": f"{numero_os:03d}",
            "{{DATA}}": data_str,
            "{{ID}}": id_texto if id_texto.strip() else "-"
        }
        
        # Substitui tags normais
        for paragrafo in doc.paragraphs:
            texto_original = "".join(run.text for run in paragrafo.runs)
            novo_texto = texto_original
            for chave, valor in mapeamento.items():
                if chave in novo_texto:
                    novo_texto = novo_texto.replace(chave, valor)
            if novo_texto != texto_original:
                for run in paragrafo.runs: run.text = ""
                if paragrafo.runs: paragrafo.runs[0].text = novo_texto

        for tabela in doc.tables:
            for linha in tabela.rows:
                for celula in linha.cells:
                    for paragrafo in celula.paragraphs:
                        texto_original = "".join(run.text for run in paragrafo.runs)
                        novo_texto = texto_original
                        for chave, valor in mapeamento.items():
                            if chave in novo_texto:
                                novo_texto = novo_texto.replace(chave, valor)
                        if novo_texto != texto_original:
                            for run in paragrafo.runs: run.text = ""
                            if paragrafo.runs: paragrafo.runs[0].text = novo_texto

        # Substitui a tag de descrição pela tabela
        for paragrafo in doc.paragraphs:
            if "{{DESCRICAO}}" in paragrafo.text:
                p = paragrafo._element
                parent = p.getparent()
                tabela = doc.add_table(rows=1, cols=2)
                tabela.style = 'Table Grid'
                tabela.columns[0].width = Inches(1.0)
                tabela.columns[1].width = Inches(5.0)
                
                hdr_cells = tabela.rows[0].cells
                hdr_cells[0].text = 'ID'
                hdr_cells[1].text = 'DESCRIÇÃO'
                
                for item in descricoes:
                    row_cells = tabela.add_row().cells
                    row_cells[0].text = item['id']
                    row_cells[1].text = item['descricao']
                
                p.addnext(tabela._element)
                parent.remove(p)
                break
        doc.save(destino_path)