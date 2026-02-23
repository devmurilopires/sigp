import customtkinter as ctk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import MaxNLocator
import textwrap
from datetime import datetime
from src.dashboard.service import DashboardService

# --- Paleta de Cores Premium ---
COLOR_BG = "#F4F6F9"          
COLOR_WHITE = "#FFFFFF"       
COLOR_PRIMARY = "#0F8C75"     # Verde Escuro
COLOR_SECONDARY = "#14B5D9"   # Azul Claro
COLOR_TEXT = "#333333"
COLOR_DANGER = "#D32F2F"      # Vermelho
COLOR_WARNING = "#F29C1F"     # Laranja

class DashboardView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        super().__init__(master, fg_color=COLOR_BG)
        self.pack(fill="both", expand=True)

        self.service = DashboardService()
        self.df_os_raw = pd.DataFrame()
        self.df_par_raw = pd.DataFrame()

        self._construir_interface()
        # Faz o carregamento completo (Banco + Tela) na inicialização
        self.atualizar_completo()

    def _construir_interface(self):
        frame_filtros = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=0, height=70)
        frame_filtros.pack(fill="x", side="top")
        frame_filtros.pack_propagate(False)

        ctk.CTkLabel(frame_filtros, text="Painel Analítico Gerencial", font=("Arial Black", 22), text_color=COLOR_PRIMARY).pack(side="left", padx=20, pady=20)

        # AGORA O BOTÃO CHAMA "atualizar_completo" PARA BUSCAR DADOS NOVOS NO BANCO!
        self.btn_filtrar = ctk.CTkButton(frame_filtros, text="🔍 ATUALIZAR", font=("Arial Bold", 13), fg_color=COLOR_PRIMARY, hover_color="#0B6B59", width=120, height=35, command=self.atualizar_completo)
        self.btn_filtrar.pack(side="right", padx=20, pady=17)

        self.cb_mes = ctk.CTkComboBox(frame_filtros, values=["Todos", "01 - Jan", "02 - Fev", "03 - Mar", "04 - Abr", "05 - Mai", "06 - Jun", "07 - Jul", "08 - Ago", "09 - Set", "10 - Out", "11 - Nov", "12 - Dez"], width=130, height=35)
        self.cb_mes.set("Todos")
        self.cb_mes.pack(side="right", padx=10, pady=17)
        ctk.CTkLabel(frame_filtros, text="Mês:", text_color="#555", font=("Arial Bold", 13)).pack(side="right")

        self.cb_ano = ctk.CTkComboBox(frame_filtros, values=[str(a) for a in range(2024, 2030)], width=100, height=35)
        self.cb_ano.set(str(datetime.now().year))
        self.cb_ano.pack(side="right", padx=10, pady=17)
        ctk.CTkLabel(frame_filtros, text="Ano:", text_color="#555", font=("Arial Bold", 13)).pack(side="right")

        self.scroll_area = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_area.pack(fill="both", expand=True, padx=10, pady=10)

        self.frame_kpis = ctk.CTkFrame(self.scroll_area, fg_color="transparent")
        self.frame_kpis.pack(fill="x", pady=(0, 15))

        self.frame_tabela = ctk.CTkFrame(self.scroll_area, fg_color="transparent")
        self.frame_tabela.pack(fill="x", pady=10)

        self.frame_graficos = ctk.CTkFrame(self.scroll_area, fg_color="transparent")
        self.frame_graficos.pack(fill="both", expand=True, pady=10)

    def criar_card(self, parent, titulo, valor, cor_destaque, icone):
        card = ctk.CTkFrame(parent, fg_color=COLOR_WHITE, corner_radius=8, border_width=1, border_color="#E0E0E0")
        barra = ctk.CTkFrame(card, fg_color=cor_destaque, width=6, corner_radius=8)
        barra.pack(side="left", fill="y")
        
        conteudo = ctk.CTkFrame(card, fg_color="transparent")
        conteudo.pack(side="left", fill="both", expand=True, padx=15, pady=10)
        
        ctk.CTkLabel(conteudo, text=titulo, font=("Arial Bold", 13), text_color="#777777").pack(anchor="w")
        
        linha_valor = ctk.CTkFrame(conteudo, fg_color="transparent")
        linha_valor.pack(fill="x", expand=True)
        ctk.CTkLabel(linha_valor, text=valor, font=("Arial Black", 32), text_color=COLOR_TEXT).pack(side="left", pady=(5,0))
        ctk.CTkLabel(linha_valor, text=icone, font=("Arial", 28)).pack(side="right", pady=(5,0))
        return card

    def _desenhar_tabela(self, df_os):
        for w in self.frame_tabela.winfo_children(): w.destroy()
        if df_os.empty: return

        itens_painel = [
            "IMPLANTAÇÃO PLACA/POSTE", "IMPLANTAÇÃO PLACA/BARROTE", "IMPLANTAÇÃO ABRIGO METÁLICO", "IMPLANTAÇÃO PARADA SEGURA",
            "TRANSFERÊNCIA PLACA/POSTE", "TRANSFERÊNCIA PLACA/BARROTE", "TRANSFERÊNCIA ABRIGO METÁLICO", "TRANSFERÊNCIA PARADA SEGURA",
            "REMOÇÃO PLACA/POSTE", "REMOÇÃO PLACA/BARROTE", "REMOÇÃO ABRIGO CONCRETO", "REMOÇÃO ABRIGO METÁLICO", "REMOÇÃO PARADA SEGURA",
            "SUBSTITUIÇÃO PLACA/POSTE", "SUBSTITUIÇÃO PLACA/BARROTE", "SUBSTITUIÇÃO ABRIGO CONCRETO", "SUBSTITUIÇÃO ABRIGO METÁLICO",
            "MANUTENÇÃO PLACA/POSTE", "MANUTENÇÃO PLACA/BARROTE", "MANUTENÇÃO ABRIGO METÁLICO", "MANUTENÇÃO PARADA SEGURA",
        ]
        colunas = ["OPERAÇÃO / PONTO DE PARADA", "JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ", "TOTAL"]
        dados_agrupados = {}
        
        for _, row in df_os.iterrows():
            chave_raw = f"{self.service.normalizar(row['tipo_os'])} {self.service.normalizar(row['tipo_item'])}"
            try: mes = row['data_dt'].month
            except: continue 
            
            if chave_raw == "REMOCAO ABRIGO CONCRETO/METALICO":
                dados_agrupados.setdefault("REMOCAO ABRIGO CONCRETO", {}).setdefault(mes, 0)
                dados_agrupados.setdefault("REMOCAO ABRIGO METALICO", {}).setdefault(mes, 0)
                dados_agrupados["REMOCAO ABRIGO CONCRETO"][mes] += 0.5
                dados_agrupados["REMOCAO ABRIGO METALICO"][mes] += 0.5
            elif chave_raw == "SUBSTITUICAO ABRIGO CONCRETO/METALICO":
                dados_agrupados.setdefault("SUBSTITUICAO ABRIGO CONCRETO", {}).setdefault(mes, 0)
                dados_agrupados.setdefault("SUBSTITUICAO ABRIGO METALICO", {}).setdefault(mes, 0)
                dados_agrupados["SUBSTITUICAO ABRIGO CONCRETO"][mes] += 0.5
                dados_agrupados["SUBSTITUICAO ABRIGO METALICO"][mes] += 0.5
            else:
                dados_agrupados.setdefault(chave_raw, {})
                dados_agrupados[chave_raw][mes] = dados_agrupados[chave_raw].get(mes, 0) + 1

        container = ctk.CTkFrame(self.frame_tabela, fg_color=COLOR_WHITE, corner_radius=8, border_width=1, border_color="#E0E0E0")
        container.pack(fill="x", padx=5)

        header_frame = ctk.CTkFrame(container, fg_color=COLOR_PRIMARY, corner_radius=6, height=35)
        header_frame.pack(fill="x", padx=2, pady=2)
        for i, col in enumerate(colunas):
            largura = 280 if i == 0 else 50
            ctk.CTkLabel(header_frame, text=col, font=("Arial Bold", 11), text_color="white", width=largura, anchor="w" if i==0 else "center").pack(side="left", fill="x", expand=True, padx=(10 if i==0 else 1))

        totais_colunas = [0] * 13 
        for idx, item_nome in enumerate(itens_painel):
            chave = self.service.normalizar(item_nome)
            meses_dict = dados_agrupados.get(chave, {})
            
            bg_color = "#F9F9F9" if idx % 2 == 0 else "#FFFFFF"
            row_frame = ctk.CTkFrame(container, fg_color=bg_color, corner_radius=0, height=28)
            row_frame.pack(fill="x", padx=2)

            ctk.CTkLabel(row_frame, text=item_nome, font=("Arial", 11), text_color="#333", anchor="w", width=280).pack(side="left", fill="x", expand=True, padx=10)

            linha_total = 0
            for m in range(1, 13):
                val = int(meses_dict.get(m, 0))
                totais_colunas[m-1] += val
                linha_total += val
                ctk.CTkLabel(row_frame, text=str(val) if val > 0 else "-", font=("Arial", 11), text_color="#555", width=50).pack(side="left", fill="x", expand=True)

            totais_colunas[12] += linha_total
            ctk.CTkLabel(row_frame, text=str(linha_total), font=("Arial Bold", 11), text_color="#000", width=50).pack(side="left", fill="x", expand=True)

        total_frame = ctk.CTkFrame(container, fg_color="#E0E4E8", corner_radius=0, height=35)
        total_frame.pack(fill="x", padx=2, pady=(0, 2))
        ctk.CTkLabel(total_frame, text="TOTAL GERAL POR MÊS", font=("Arial Black", 12), text_color=COLOR_PRIMARY, anchor="w", width=280).pack(side="left", fill="x", expand=True, padx=10)
        for val in totais_colunas:
             ctk.CTkLabel(total_frame, text=str(val), font=("Arial Black", 12), text_color=COLOR_PRIMARY, width=50).pack(side="left", fill="x", expand=True)


    def _configurar_eixo(self, ax, titulo):
        ax.set_title(titulo, fontsize=12, fontweight='bold', color="#444", pad=15)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#DDDDDD')
        ax.spines['bottom'].set_color('#DDDDDD')
        ax.tick_params(colors='#555555')
        ax.grid(axis='y', linestyle='--', alpha=0.3, color='#DDDDDD') 
        ax.set_facecolor(COLOR_WHITE)

    # =========================================================
    # FUNÇÃO QUE RESOLVE TUDO (TEMPO REAL E GRÁFICOS)
    # =========================================================
    def atualizar_completo(self):
        """Busca do banco novamente E atualiza os gráficos"""
        self.df_os_raw, self.df_par_raw = self.service.carregar_dados_brutos()
        self.atualizar_dashboard()

    def atualizar_dashboard(self):
        try: ano_sel = int(self.cb_ano.get())
        except: ano_sel = datetime.now().year
        
        mes_str = self.cb_mes.get()
        mes_sel = int(mes_str.split(" - ")[0]) if mes_str != "Todos" else None

        df_os_f, df_par_f = self.service.filtrar_dados(self.df_os_raw, self.df_par_raw, ano_sel, mes_sel)

        # 1. CARDS
        for w in self.frame_kpis.winfo_children(): w.destroy()
        c_os, c_par, c_def, c_indef = self.service.calcular_kpis(df_os_f, df_par_f)
        
        self.frame_kpis.columnconfigure((0,1,2,3), weight=1)
        self.criar_card(self.frame_kpis, "TOTAL DE ORDENS (OS)", f"{c_os}", COLOR_PRIMARY, "📋").grid(row=0, column=0, padx=8, sticky="ew")
        self.criar_card(self.frame_kpis, "TOTAL DE PARECERES", f"{c_par}", COLOR_SECONDARY, "📝").grid(row=0, column=1, padx=8, sticky="ew")
        self.criar_card(self.frame_kpis, "PARECERES DEFERIDOS", f"{c_def}", "#28A745", "✅").grid(row=0, column=2, padx=8, sticky="ew")
        self.criar_card(self.frame_kpis, "PARECERES INDEFERIDOS", f"{c_indef}", COLOR_DANGER, "❌").grid(row=0, column=3, padx=8, sticky="ew")

        # 2. TABELA
        self._desenhar_tabela(df_os_f)

        # 3. GRÁFICOS
        for w in self.frame_graficos.winfo_children(): w.destroy()
        
        fig, axs = plt.subplots(4, 2, figsize=(14, 23), facecolor=COLOR_WHITE)
        fig.patch.set_facecolor(COLOR_WHITE)

        if df_os_f.empty and df_par_f.empty:
            axs[0,0].text(0.5, 0.5, "Sem dados para o filtro selecionado", ha='center', fontsize=14)
        else:
            meses_pt = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            meses_en = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

            # ----------------------------------------------------
            # LINHA 1: Evolução Temporal
            # ----------------------------------------------------
            # 0,0: Evolução OS
            ax = axs[0, 0]
            if not df_os_f.empty:
                counts = df_os_f['data_dt'].dt.month_name().value_counts().reindex(meses_en, fill_value=0)
                counts.index = meses_pt
                bars = ax.bar(counts.index, counts.values, color=COLOR_PRIMARY, width=0.6)
                max_val = max(counts.values) if len(counts)>0 else 1
                ax.set_ylim(0, max_val * 1.15) # Aumenta o teto do gráfico em 15%
                for bar in bars:
                    h = bar.get_height()
                    if h > 0: ax.text(bar.get_x() + bar.get_width()/2, h + (max_val*0.02), f'{int(h)}', ha='center', va='bottom', fontweight='bold', color=COLOR_PRIMARY)
            self._configurar_eixo(ax, f"Evolução de OS Criadas ({ano_sel})")

            # 0,1: Evolução Pareceres
            ax = axs[0, 1]
            if not df_par_f.empty:
                counts = df_par_f['data_dt'].dt.month_name().value_counts().reindex(meses_en, fill_value=0)
                counts.index = meses_pt
                bars = ax.bar(counts.index, counts.values, color=COLOR_SECONDARY, width=0.6)
                max_val = max(counts.values) if len(counts)>0 else 1
                ax.set_ylim(0, max_val * 1.15)
                for bar in bars:
                    h = bar.get_height()
                    if h > 0: ax.text(bar.get_x() + bar.get_width()/2, h + (max_val*0.02), f'{int(h)}', ha='center', va='bottom', fontweight='bold', color=COLOR_SECONDARY)
            self._configurar_eixo(ax, f"Evolução de Pareceres Gerados ({ano_sel})")


            # ----------------------------------------------------
            # LINHA 2: Carga de Trabalho e Produtividade (%)
            # ----------------------------------------------------
            # 1,0: Top 8 Solicitantes
            ax = axs[1, 0]
            if not df_par_f.empty and 'solicitante' in df_par_f.columns:
                counts = df_par_f['solicitante'].replace("", "Não Informado").fillna("Não Informado").value_counts().head(8)
                labels = [textwrap.fill(str(nome), width=25) for nome in counts.index]
                bars = ax.barh(labels, counts.values, color="#F24822")
                ax.invert_yaxis()
                max_val = max(counts.values) if len(counts)>0 else 1
                ax.set_xlim(0, max_val * 1.25) # Espaço lateral extra
                for bar in bars:
                    w = bar.get_width()
                    if w > 0: ax.text(w + (max_val*0.02), bar.get_y() + bar.get_height()/2, f'{int(w)}', va='center', ha='left', fontweight='bold', color='#F24822')
            self._configurar_eixo(ax, "Volume por Solicitante (Pareceres)")

            # 1,1: Participação % (Share of Work)
            ax = axs[1, 1]
            s1 = df_os_f['criado_por'].value_counts() if not df_os_f.empty else pd.Series()
            s2 = df_par_f['criado_por'].value_counts() if not df_par_f.empty else pd.Series()
            prod_total = s1.add(s2, fill_value=0).sort_values(ascending=False).head(8)
            total_geral_sistema = len(df_os_f) + len(df_par_f)
            
            if not prod_total.empty and total_geral_sistema > 0:
                labels = [textwrap.fill(str(nome), width=20) for nome in prod_total.index]
                bars = ax.barh(labels, prod_total.values, color="#8E44AD")
                ax.invert_yaxis()
                max_val = max(prod_total.values) if len(prod_total)>0 else 1
                ax.set_xlim(0, max_val * 1.35) # Espaço gigante para caber a porcentagem
                for bar in bars:
                    w = bar.get_width()
                    if w > 0: 
                        pct = (w / total_geral_sistema) * 100
                        ax.text(w + (max_val*0.02), bar.get_y() + bar.get_height()/2, f"{int(w)} unid. ({pct:.1f}%)", va='center', ha='left', fontweight='bold', color='#8E44AD')
            self._configurar_eixo(ax, "Produtividade Relativa (Carga de Trabalho %)")


            # ----------------------------------------------------
            # LINHA 3: Qualidade e Status (Donut Charts)
            # ----------------------------------------------------
            # 2,0: Status OS
            ax = axs[2, 0]
            if not df_os_f.empty and 'status_conclusao' in df_os_f.columns:
                status_counts = df_os_f['status_conclusao'].fillna("NÃO").value_counts()
                if not status_counts.empty:
                    cores_map = {"SIM": "#28A745", "NÃO": COLOR_DANGER, "NÃO AUTORIZADA": COLOR_WARNING}
                    cores_grafico = [cores_map.get(str(x).upper(), "#999999") for x in status_counts.index]
                    ax.pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%', startangle=90, colors=cores_grafico, textprops={'fontsize': 11, 'fontweight': 'bold'}, wedgeprops=dict(width=0.4, edgecolor='w'))
                    ax.set_title("Status das Ordens de Serviço", fontsize=12, fontweight='bold', color="#444", pad=15)
            else:
                self._configurar_eixo(ax, "Status das Ordens de Serviço")
                ax.text(0.5, 0.5, "Sem dados", ha='center')

            # 2,1: Aprovação Pareceres
            ax = axs[2, 1]
            if not df_par_f.empty and 'tipo' in df_par_f.columns:
                taxa_counts = df_par_f['tipo'].str.upper().value_counts()
                if not taxa_counts.empty:
                    cores_map = {"DEFERIDO": "#28A745", "INDEFERIDO": COLOR_DANGER}
                    cores_grafico = [cores_map.get(str(x), "#999999") for x in taxa_counts.index]
                    ax.pie(taxa_counts.values, labels=taxa_counts.index, autopct='%1.1f%%', startangle=90, colors=cores_grafico, textprops={'fontsize': 11, 'fontweight': 'bold'}, wedgeprops=dict(width=0.4, edgecolor='w'))
                    ax.set_title("Taxa de Aprovação (Pareceres)", fontsize=12, fontweight='bold', color="#444", pad=15)
            else:
                self._configurar_eixo(ax, "Taxa de Aprovação (Pareceres)")
                ax.text(0.5, 0.5, "Sem dados", ha='center')


            # ----------------------------------------------------
            # LINHA 4: Natureza do Serviço (CORRIGIDO ROTAÇÃO DOS NOMES)
            # ----------------------------------------------------
            # 3,0: Natureza Ação OS
            ax = axs[3, 0]
            if not df_os_f.empty and 'tipo_os' in df_os_f.columns:
                counts = df_os_f['tipo_os'].str.upper().value_counts().head(5)
                labels = [textwrap.fill(str(nome), width=12) for nome in counts.index] # Quebra de linha
                bars = ax.bar(labels, counts.values, color="#34495E", width=0.5)
                max_val = max(counts.values) if len(counts)>0 else 1
                ax.set_ylim(0, max_val * 1.2)
                
                # ROTACIONA OS TEXTOS PARA NÃO ENCAVALAREM
                ax.set_xticks(range(len(labels)))
                ax.set_xticklabels(labels, rotation=20, ha='right', fontsize=9)
                
                for bar in bars:
                    h = bar.get_height()
                    if h > 0: ax.text(bar.get_x() + bar.get_width()/2, h + (max_val*0.02), f'{int(h)}', ha='center', va='bottom', fontweight='bold', color="#34495E")
            self._configurar_eixo(ax, "Natureza da Ação (OS)")

            # 3,1: Tipos de Itens
            ax = axs[3, 1]
            if not df_os_f.empty and 'tipo_item' in df_os_f.columns:
                counts = df_os_f['tipo_item'].str.upper().value_counts().head(5)
                labels = [textwrap.fill(str(nome), width=15) for nome in counts.index] # Quebra de linha
                bars = ax.bar(labels, counts.values, color="#E67E22", width=0.5)
                max_val = max(counts.values) if len(counts)>0 else 1
                ax.set_ylim(0, max_val * 1.2)
                
                # ROTACIONA OS TEXTOS PARA NÃO ENCAVALAREM
                ax.set_xticks(range(len(labels)))
                ax.set_xticklabels(labels, rotation=20, ha='right', fontsize=9)
                
                for bar in bars:
                    h = bar.get_height()
                    if h > 0: ax.text(bar.get_x() + bar.get_width()/2, h + (max_val*0.02), f'{int(h)}', ha='center', va='bottom', fontweight='bold', color="#E67E22")
            self._configurar_eixo(ax, "Tipos de Itens Mais Demandados (OS)")

        fig.tight_layout(pad=4.0, h_pad=5.0)

        canvas = FigureCanvasTkAgg(fig, master=self.frame_graficos)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

def renderizar(frame_destino, usuario_logado):
    return DashboardView(master=frame_destino, usuario_logado=usuario_logado)