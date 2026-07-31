import pandas as pd
import math
import unicodedata
from datetime import datetime, time
from numbers import Number
from pathlib import Path
import re
from src.modulos.quadro_horario.pesquisas.repository import PesquisaQuadroHorarioRepository

class PesquisaQuadroHorarioService:
    def __init__(self):
        self.repo = PesquisaQuadroHorarioRepository()

    def buscar_sugestoes_linhas(self):
        return self.repo.buscar_linhas()

    def salvar_dados(self, linha, tipo, dados_completos, usuario):
        codigo_linha = linha.split(" - ")[0].strip() if " - " in linha else linha.strip()
        
        nome_tipo = "%TEMPO%" if tipo == "tempo" else "%DEMANDA%"

        datas_raw = dados_completos.get("datas", [])
        datas_formatadas = []
        for d in datas_raw:
            try:
                dt_obj = datetime.strptime(d, "%d/%m/%Y").date()
                datas_formatadas.append(dt_obj)
            except Exception:
                pass

        return self.repo.salvar_pesquisa(codigo_linha, nome_tipo, datas_formatadas, dados_completos, usuario)
    
    # --- Utilitários Internos ---
    def _normalizar_nome(self, s):
        if pd.isna(s) or not isinstance(s, str): return ""
        s = s.lower().strip()
        s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
        # BLINDAGEM MÁXIMA: Arranca qualquer espaço escondido, \n, \t ou símbolo especial
        s = re.sub(r'[^a-z0-9]', '', s) 
        return s

    def _extrair_nome_sentido(self, trajeto):
        if not isinstance(trajeto, str): return ""
        trajeto = trajeto.upper()
        return trajeto.split("SENTIDO", 1)[1].strip() if "SENTIDO" in trajeto else trajeto.strip()

    def _extrair_hora(self, v):
        if pd.isna(v): return None
        if isinstance(v, (time, datetime)): return v.hour

        # O Excel grava horas como frações de um dia (por exemplo, 0.5 = 12:00).
        # Sem esse tratamento o pandas interpreta 0.5 como 00:00:00 de 1970.
        if isinstance(v, Number) and not isinstance(v, bool):
            numero = float(v)
            if 0 <= numero <= 1:
                return int((numero % 1) * 24)
            if numero.is_integer() and 0 <= numero <= 23:
                return int(numero)

        texto = str(v).strip()
        correspondencia = re.match(r"^(\d{1,2})\s*:", texto)
        if correspondencia:
            hora = int(correspondencia.group(1))
            return hora if 0 <= hora <= 23 else None
        try:
            ts = pd.to_datetime(v, errors='coerce')
            if pd.isna(ts): return None
            return int(ts.hour)
        except (TypeError, ValueError, OverflowError):
            return None

    def _normalizar_tempo(self, v):
        if pd.isna(v): return ""
        if isinstance(v, (time, datetime)): return v.strftime("%H:%M:%S")
        if isinstance(v, Number):
            fv = float(v)
            sec = int(round(fv * 86400.0)) if abs(fv) <= 1.0 else int(round(fv))
            return f"{sec//3600:02d}:{(sec%3600)//60:02d}:{sec%60:02d}"
        texto = str(v).strip()
        # "01:30" em uma planilha representa normalmente 1h30, mas o pandas o
        # interpreta como 1 minuto e 30 segundos caso não tenha os segundos.
        if re.fullmatch(r"\d{1,2}:\d{2}", texto):
            return f"{texto}:00"
        return texto

    def _ler_excel(self, caminho):
        """Lê a planilha usando o motor compatível e nunca deixa erro chegar à UI."""
        extensao = Path(caminho).suffix.lower()
        motores = {
            ".xls": "xlrd",
            ".xlsx": "openpyxl",
            ".xlsm": "openpyxl",
            ".xltx": "openpyxl",
            ".xltm": "openpyxl",
        }
        motor = motores.get(extensao)
        if not motor:
            return False, "Formato não suportado. Selecione um arquivo Excel .xlsx, .xls ou .xlsm."
        try:
            return True, pd.read_excel(caminho, engine=motor)
        except ImportError:
            if motor == "xlrd":
                return False, (
                    "Não foi possível abrir este arquivo .xls (Excel antigo), pois o suporte "
                    "necessário não está instalado. Instale 'xlrd>=2.0.1' e abra novamente, "
                    "ou salve o arquivo como .xlsx no Excel."
                )
            return False, "Não foi possível abrir arquivos .xlsx porque o suporte openpyxl não está instalado."
        except (FileNotFoundError, PermissionError) as erro:
            return False, f"Não foi possível acessar a planilha: {erro}"
        except Exception as erro:
            return False, f"Não foi possível ler a planilha. Verifique se ela não está corrompida. Detalhe: {erro}"

    def _tempo_para_minutos(self, valor, numero_em_minutos=False):
        """Converte durações do Excel (hora, texto ou número) para minutos."""
        if pd.isna(valor):
            return None
        # No quadro atual, números inteiros normalmente já são minutos. Frações
        # menores que 1, porém, continuam sendo horários/durações do Excel.
        if numero_em_minutos and isinstance(valor, Number) and not isinstance(valor, bool) and abs(float(valor)) > 1:
            return float(valor)
        duracao = pd.to_timedelta(self._normalizar_tempo(valor), errors="coerce")
        return None if pd.isna(duracao) else duracao.total_seconds() / 60.0

    def _numero_excel(self, valor):
        if pd.isna(valor):
            return None
        if isinstance(valor, Number) and not isinstance(valor, bool):
            return float(valor)
        texto = str(valor).strip()
        if not texto:
            return None
        # Aceita tanto 1.234,50 quanto 1,234.50.
        if "," in texto and "." in texto:
            texto = texto.replace(".", "").replace(",", ".") if texto.rfind(",") > texto.rfind(".") else texto.replace(",", "")
        else:
            texto = texto.replace(",", ".")
        try:
            return float(texto)
        except ValueError:
            return None

    def _separar_blocos(self, df, col_trajeto):
        blank_mask = df[col_trajeto].isna() | (df[col_trajeto].astype(str).str.strip() == "")
        blank_idxs = df[blank_mask].index.tolist()
        blocks, start = [], 0
        for bi in blank_idxs:
            if not df.iloc[start:bi].empty: blocks.append(df.iloc[start:bi].copy())
            start = bi + 1
        if not df.iloc[start:].empty: blocks.append(df.iloc[start:].copy())
        return blocks

    def _encontrar_coluna(self, colunas, chaves):
        col_map = {self._normalizar_nome(str(c)): c for c in colunas}
        for chave in chaves:
            if chave in col_map: return col_map[chave]
        for chave in chaves:
            for norm_col, orig_col in col_map.items():
                if chave in norm_col:
                    return orig_col
        return None

    # --- PROCESSAMENTO: TEMPO DE VIAGEM ---
    def processar_excel_tempo(self, caminho, nomes_sentidos):
        sucesso, df_ou_erro = self._ler_excel(caminho)
        if not sucesso:
            return False, df_ou_erro
        df = df_ou_erro
        
        t_col = self._encontrar_coluna(df.columns, ["trajeto", "rota", "sentido", "linha"])
        p_col = self._encontrar_coluna(df.columns, ["partidareal", "partida", "hora", "real", "inicio"])
        tv_col = self._encontrar_coluna(df.columns, ["tempoviagem", "tempo", "tv", "duracao", "viagem"])
        
        if not (t_col and p_col and tv_col): 
            return False, f"Este quadro (Tempo de Viagem) precisa de: Trajeto, Partida Real e Tempo.\nColunas lidas no seu Excel: {', '.join(str(c) for c in df.columns)}"
        
        blocos = self._separar_blocos(df[[t_col, p_col, tv_col]].copy(), t_col)
        if not blocos: return False, "Nenhum dado válido encontrado. Certifique-se de separar os sentidos com uma linha em branco."

        sentidos = {}
        for i, bloco in enumerate(blocos, start=1):
            bloco["Hora"] = bloco[p_col].apply(self._extrair_hora)
            bloco["TempoMin"] = bloco[tv_col].apply(self._tempo_para_minutos)
            
            bloco = bloco[bloco["Hora"].notna() & bloco["TempoMin"].notna()]
            if bloco.empty: continue

            medias = bloco.groupby("Hora")["TempoMin"].mean()
            nome_norm = self._normalizar_nome(self._extrair_nome_sentido(bloco[t_col].iloc[0]))
            col_alvo = nomes_sentidos.get(nome_norm, f"s{i}")
            sentidos[col_alvo] = {int(h): math.ceil(float(m)) for h, m in medias.items()}
        return (True, sentidos) if sentidos else (False, "Nenhum horário e tempo de viagem válido foi encontrado na planilha.")

    def processar_excel_verde(self, caminho, nomes_sentidos):
        sucesso, df_ou_erro = self._ler_excel(caminho)
        if not sucesso:
            return False, df_ou_erro
        df = df_ou_erro
        
        t_col = self._encontrar_coluna(df.columns, ["trajeto", "rota", "sentido", "linha"])
        p_col = self._encontrar_coluna(df.columns, ["partidaplanejada", "planejada", "partida", "hora"])
        tv_col = self._encontrar_coluna(df.columns, ["tv", "tempoviagem", "tempo", "duracao", "viagem"])
        
        if not (t_col and p_col and tv_col): 
            return False, f"Este quadro (Quadro Atual) precisa de: Trajeto, Partida Planejada e TV.\nColunas lidas no seu Excel: {', '.join(str(c) for c in df.columns)}"
        
        blocos = self._separar_blocos(df[[t_col, p_col, tv_col]].copy(), t_col)
        sentidos = {}
        for i, bloco in enumerate(blocos, start=1):
            bloco["Hora"] = bloco[p_col].apply(self._extrair_hora)
            bloco["TempoMin"] = bloco[tv_col].apply(lambda valor: self._tempo_para_minutos(valor, numero_em_minutos=True))
            bloco = bloco[bloco["Hora"].notna() & bloco["TempoMin"].notna()]
            if bloco.empty: continue

            medias = bloco.groupby("Hora")["TempoMin"].mean()
            nome_norm = self._normalizar_nome(self._extrair_nome_sentido(bloco[t_col].iloc[0]))
            col_alvo = nomes_sentidos.get(nome_norm, f"s{i}")
            sentidos[col_alvo] = {int(h): math.ceil(float(m)) for h, m in medias.items()}
        return (True, sentidos) if sentidos else (False, "Nenhum horário e TV válido foi encontrado na planilha.")

    # --- PROCESSAMENTO: DEMANDA ---
    def processar_excel_demanda(self, caminho, nomes_sentidos):
        sucesso, df_ou_erro = self._ler_excel(caminho)
        if not sucesso:
            return False, df_ou_erro
        df = df_ou_erro
        
        t_col = self._encontrar_coluna(df.columns, ["trajeto", "rota", "sentido", "linha"])
        p_col = self._encontrar_coluna(df.columns, ["partidareal", "partida", "hora", "real"])
        pass_col = self._encontrar_coluna(df.columns, ["passageiro", "passag", "pax", "total", "demanda", "qtd"])
        
        if not (t_col and p_col and pass_col): 
            return False, f"Este quadro (Relatório Demanda) precisa de: Trajeto, Partida Real e Passageiro.\nColunas lidas no seu Excel: {', '.join(str(c) for c in df.columns)}"
        
        blocos = self._separar_blocos(df[[t_col, p_col, pass_col]].copy(), t_col)
        sentidos = {}
        for i, bloco in enumerate(blocos, start=1):
            bloco["Hora"] = bloco[p_col].apply(self._extrair_hora)
            bloco[pass_col] = bloco[pass_col].apply(self._numero_excel)
            bloco = bloco[bloco["Hora"].notna() & bloco[pass_col].notna()]
            if bloco.empty: continue

            somas = bloco.groupby("Hora")[pass_col].sum()
            nome_norm = self._normalizar_nome(self._extrair_nome_sentido(bloco[t_col].iloc[0]))
            col_alvo = nomes_sentidos.get(nome_norm, f"s{i}")
            sentidos[col_alvo] = {int(h): int(round(float(s))) for h, s in somas.items()}
        return (True, sentidos) if sentidos else (False, "Nenhum horário e quantidade de passageiros válida foi encontrada na planilha.")

    def processar_excel_viagens(self, caminho, nomes_sentidos):
        sucesso, df_ou_erro = self._ler_excel(caminho)
        if not sucesso:
            return False, df_ou_erro
        df = df_ou_erro
        
        t_col = self._encontrar_coluna(df.columns, ["trajeto", "rota", "sentido", "linha"])
        p_col = self._encontrar_coluna(df.columns, ["partidaplanejada", "planejada", "partida", "hora"])
        
        if not (t_col and p_col): 
            return False, f"Este quadro (Nº de Viagens) precisa de: Trajeto e Partida Planejada.\nColunas lidas no seu Excel: {', '.join(str(c) for c in df.columns)}"

        blocos = self._separar_blocos(df[[t_col, p_col]].copy(), t_col)
        viagens = {}
        for i, bloco in enumerate(blocos, start=1):
            bloco["Hora"] = bloco[p_col].apply(self._extrair_hora)
            bloco = bloco[bloco["Hora"].notna()]
            if bloco.empty: continue

            contagens = bloco.groupby("Hora").size()
            nome_norm = self._normalizar_nome(self._extrair_nome_sentido(bloco[t_col].iloc[0]))
            col_alvo = nomes_sentidos.get(nome_norm, f"s{i}")
            viagens[col_alvo] = {int(h): int(c) for h, c in contagens.items()}
        return (True, viagens) if viagens else (False, "Nenhuma partida planejada válida foi encontrada na planilha.")
