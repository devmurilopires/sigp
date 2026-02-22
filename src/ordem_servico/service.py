import os
import unicodedata
from datetime import datetime
from docx import Document
from docx.shared import Inches
from src.ordem_servico.repository import OSRepository

# Tenta puxar o utils da raiz ou da pasta shared
try:
    from src.shared.utils import resource_path
except ImportError:
    try:
        from src.shared.utils import resource_path
    except ImportError:
        def resource_path(path): return path

class OSService:
    def __init__(self):
        # Conecta o serviço ao repositório (banco de dados)
        self.repo = OSRepository()

    # =========================================================
    # REGRAS DE NEGÓCIO E VALIDAÇÕES
    # =========================================================
    def normalizar(self, texto: str) -> str:
        """Remove acentos e deixa a string em caixa alta para padronização no banco."""
        if not texto: return ""
        nfkd = unicodedata.normalize('NFKD', texto)
        sem_acentos = "".join(c for c in nfkd if not unicodedata.combining(c))
        return sem_acentos.upper()

    def consultar_endereco(self, id_procurado):
        """Busca os dados do endereço no repositório para preencher a tela."""
        return self.repo.buscar_endereco_por_id(id_procurado)

    def obter_historico_formatado(self, id_procurado):
        """Busca o histórico de OS desse ID e formata em texto para mostrar no popup."""
        historico = self.repo.buscar_historico_os(id_procurado)
        if not historico:
            return "Nenhuma movimentação de Ordem de Serviço encontrada para este ID."
        
        texto = ""
        for r in historico:
            texto += f"OS: {r[0]} | Data: {r[1]} | Tipo: {r[2]} | Item: {r[3]}\nEndereço: {r[4]} - Bairro: {r[5]}\nCriado por: {r[6]}\n"
            texto += "-" * 50 + "\n"
        return texto

    # =========================================================
    # ORQUESTRAÇÃO PRINCIPAL (GERAR O.S E SALVAR)
    # =========================================================
    def processar_criacao_os(self, descricoes_acumuladas, pasta_escolhida, modelo_escolhido, tipo_os, tipo_item, form_dados, usuario_logado):
        """Método principal que coordena a geração do arquivo e os salvamentos no banco."""
        
        if not descricoes_acumuladas:
            return False, "Adicione pelo menos um item (descrição) na lista antes de gerar a OS."

        # 1. Definição de Caminhos na Rede
        if pasta_escolhida == "URBMIDIA":
            pasta_base = r"C:\Users\sousa\OneDrive\Documentos\pastasTeste\OS Paradas\SIGP\2026\URBMÍDIA - SIGP"
        else:
            pasta_base = r"C:\Users\sousa\OneDrive\Documentos\pastasTeste\OS Paradas\SIGP\2026\PROXIMA PARADA - SIGP"

        if not os.path.exists(pasta_base):
            return False, f"A pasta de rede não está acessível no momento:\n{pasta_base}"

        # 2. Prepara os IDs
        ids_unicos = list(set([d["id"] for d in descricoes_acumuladas]))
        ids_formatado = "-".join(ids_unicos)
        id_principal = descricoes_acumuladas[0]["id"]

        # 3. Gerencia Endereços (Cadastra novos ou atualiza/reativa existentes)
        for id_atual in ids_unicos:
            dados_id = self.repo.buscar_endereco_por_id(id_atual)
            try:
                if not dados_id:
                    # ID não existia, cria um novo
                    self.repo.cadastrar_endereco(
                        id_atual, form_dados['endereco'], form_dados['numero'], 
                        form_dados['bairro'], form_dados['complemento'], usuario_logado
                    )
                else:
                    # ID já existia, atualiza os dados. Se estava INATIVO, reativa.
                    reativar = dados_id["status"].strip().upper() == "INATIVO"
                    self.repo.atualizar_endereco(
                        id_atual, form_dados['endereco'], form_dados['numero'], 
                        form_dados['bairro'], form_dados['complemento'], usuario_logado, reativar=reativar
                    )
            except Exception as e:
                return False, str(e)

        # 4. Preparação dos dados para o Documento e Banco de Dados
        ano_atual = datetime.now().strftime('%Y')
        numero_os = self.repo.obter_proximo_numero_os(pasta_escolhida, ano_atual)
        data_str = datetime.now().strftime("%d/%m/%Y")

        # Tratamento da String de Endereço baseada na primeira descrição
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
            pass # Se der erro no split, mantém os dados originais do form_dados

        # 5. Criação das Pastas e Geração do Arquivo Word (.docx)
        nome_pasta = f"{numero_os:03d}-{datetime.now().strftime('%m')}-{ano_atual}-ID{'-'.join(ids_unicos) if ids_unicos else 'EMERGENCIA'}"
        caminho_pasta = os.path.join(pasta_base, nome_pasta)
        os.makedirs(caminho_pasta, exist_ok=True)

        nome_arquivo = f"O.S {numero_os:03d}-{ano_atual}-ID{'-'.join(ids_unicos) if ids_unicos else 'EMERGENCIA'}.docx"
        destino_docx = os.path.join(caminho_pasta, nome_arquivo)

        try:
            caminho_modelo = resource_path(modelo_escolhido)
            self._gerar_documento_modelo(caminho_modelo, destino_docx, numero_os, data_str, id_principal, descricoes_acumuladas)
        except Exception as e:
            return False, f"Erro ao gerar o arquivo Word da OS:\n{e}"

        # 6. Salvar Registro da OS no Banco de Dados
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
            return True, f"Ordem de Serviço criada e registrada com sucesso!\nSalva em: {nome_arquivo}"
        except Exception as e:
            return False, str(e)

    # =========================================================
    # MANIPULAÇÃO DO WORD (DOCX)
    # =========================================================
    def _gerar_documento_modelo(self, modelo_path, destino_path, numero_os, data_str, id_texto, descricoes):
        """Abre o modelo do Word, substitui as tags e gera a tabela de descrições."""
        doc = Document(modelo_path)
        mapeamento = {
            "{{NUMERO_OS}}": f"{numero_os:03d}",
            "{{DATA}}": data_str,
            "{{ID}}": id_texto if id_texto.strip() else "-"
        }
        
        # 1. Substitui tags normais nos parágrafos soltos
        for paragrafo in doc.paragraphs:
            texto_original = "".join(run.text for run in paragrafo.runs)
            novo_texto = texto_original
            for chave, valor in mapeamento.items():
                if chave in novo_texto:
                    novo_texto = novo_texto.replace(chave, valor)
            if novo_texto != texto_original:
                for run in paragrafo.runs: run.text = ""
                if paragrafo.runs: paragrafo.runs[0].text = novo_texto

        # 2. Substitui tags normais dentro de tabelas existentes (ex: cabeçalho)
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

        # 3. Encontra a tag {{DESCRICAO}} e a substitui por uma Tabela Dinâmica
        for paragrafo in doc.paragraphs:
            if "{{DESCRICAO}}" in paragrafo.text:
                p = paragrafo._element
                parent = p.getparent()
                
                # Cria a tabela de itens
                tabela = doc.add_table(rows=1, cols=2)
                tabela.style = 'Table Grid'
                tabela.columns[0].width = Inches(1.0)
                tabela.columns[1].width = Inches(5.0)
                
                # Cabeçalhos da tabela
                hdr_cells = tabela.rows[0].cells
                hdr_cells[0].text = 'ID'
                hdr_cells[1].text = 'DESCRIÇÃO'
                
                # Linhas dinâmicas
                for item in descricoes:
                    row_cells = tabela.add_row().cells
                    row_cells[0].text = item['id']
                    row_cells[1].text = item['descricao']
                
                # Insere a tabela no lugar do parágrafo da tag e remove a tag
                p.addnext(tabela._element)
                parent.remove(p)
                break
        
        # Salva o documento no destino na rede
        doc.save(destino_path)