import customtkinter as ctk
from tkinter import messagebox
from src.ordem_servico.service import OSService

class OSView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        # Inicializa o Frame (herdando o fundo branco padrão das abas)
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True)

        # Injeta o Service e Dados do Usuário
        self.service = OSService()
        self.usuario_logado = usuario_logado.get('nome') if isinstance(usuario_logado, dict) else usuario_logado
        self.descricoes_acumuladas = []

        self.itens_urbmidia = ["Abrigo Metálico", "Parada Segura", "Abrigo Concreto"]
        self.itens_proximaparada = ["Placa/Barrote", "Placa/Poste"]

        self._construir_interface()

    def _construir_interface(self):
        # Container Scrollável
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#FFFFFF")
        self.scroll_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # --- CABEÇALHO (Seletor de Modelo) ---
        header_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(header_frame, text="Gerador de Ordem de Serviço", font=("Arial Black", 24), text_color="#0F8C75").pack(side="left")
        
        self.pasta_escolhida_var = ctk.StringVar(value="URBMIDIA")
        self.pasta_escolhida_var.trace_add("write", self._atualizar_opcoes_item)

        ctk.CTkRadioButton(header_frame, text="PROXIMA PARADA", variable=self.pasta_escolhida_var, value="PROXIMAPARADA", fg_color="#0F8C75").pack(side="right", padx=10)
        ctk.CTkRadioButton(header_frame, text="URBMÍDIA", variable=self.pasta_escolhida_var, value="URBMIDIA", fg_color="#0F8C75").pack(side="right", padx=10)
        ctk.CTkLabel(header_frame, text="Modelo:", font=("Arial Bold", 14)).pack(side="right", padx=10)

        # --- FORMULÁRIO ---
        form_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#F2F2F2", corner_radius=10)
        form_frame.pack(fill="x", pady=10, padx=10)

        # Linha 1: ID, Tipo OS, Tipo Item
        row1 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row1.pack(fill="x", pady=10, padx=15)

        self.id_entry = self._criar_campo(row1, "ID do Ponto", width=200, side="left")
        self.id_entry.bind("<FocusOut>", self.ao_sair_do_id)

        self.tipo_os_var = ctk.CTkComboBox(row1, values=["Implantação", "Transferência", "Remoção", "Substituição", "Manutenção"], state="readonly", width=250)
        self.tipo_os_var.set("Implantação")
        self._empacotar_campo(row1, "Ação da OS", self.tipo_os_var, side="left")

        self.tipo_item_var = ctk.CTkComboBox(row1, values=self.itens_urbmidia, state="readonly", width=250)
        self.tipo_item_var.set(self.itens_urbmidia[0])
        self._empacotar_campo(row1, "Tipo de Item", self.tipo_item_var, side="left")

        # Linha 2: Endereço, Número
        row2 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row2.pack(fill="x", pady=10, padx=15)
        
        self.endereco_entry = self._criar_campo(row2, "Logradouro (Endereço)", width=550, side="left")
        self.numero_entry = self._criar_campo(row2, "Número", width=150, side="left")

        # Linha 3: Bairro, Complemento
        row3 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row3.pack(fill="x", pady=10, padx=15)

        self.bairro_entry = self._criar_campo(row3, "Bairro", width=350, side="left")
        self.complemento_entry = self._criar_campo(row3, "Complemento", width=350, side="left")

        # Botão Adicionar
        ctk.CTkButton(form_frame, text="➕ Adicionar à Lista", fg_color="#0F8C75", font=("Arial Bold", 14), height=40, command=self.adicionar_descricao).pack(pady=20)

        # --- TABELA DE ACUMULADOS ---
        tabela_container = ctk.CTkFrame(self.scroll_frame, fg_color="#F2F2F2", corner_radius=10)
        tabela_container.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(tabela_container, text="Itens da OS (Descrições Acumuladas)", font=("Arial Bold", 16), text_color="#333333").pack(anchor="w", padx=15, pady=(15,5))
        
        self.tabela_frame = ctk.CTkFrame(tabela_container, fg_color="transparent")
        self.tabela_frame.pack(fill="both", expand=True, padx=15, pady=10)

        # --- RODAPÉ (Gerar OS) ---
        footer_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        footer_frame.pack(fill="x", pady=20)

        self.criado_por_label = ctk.CTkLabel(footer_frame, text=f"Responsável: {self.usuario_logado}", font=("Arial", 12), text_color="gray")
        self.criado_por_label.pack(side="left", padx=10)

        ctk.CTkButton(footer_frame, text="✅ GERAR ORDEM DE SERVIÇO", fg_color="#14A1D9", font=("Arial Bold", 16), height=50, width=300, command=self.acao_criar_os).pack(side="right", padx=10)

    # --- Utilitários de UI ---
    def _criar_campo(self, parent, label_text, width, side="top"):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(side=side, padx=10, fill="x")
        ctk.CTkLabel(container, text=label_text, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        entry = ctk.CTkEntry(container, width=width, height=35)
        entry.pack(anchor="w", pady=(2,0))
        return entry
        
    def _empacotar_campo(self, parent, label_text, widget, side="top"):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(side=side, padx=10, fill="x")
        ctk.CTkLabel(container, text=label_text, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        widget.pack(anchor="w", pady=(2,0))

    def _atualizar_opcoes_item(self, *args):
        if self.pasta_escolhida_var.get() == "URBMIDIA":
            self.tipo_item_var.configure(values=self.itens_urbmidia)
            self.tipo_item_var.set(self.itens_urbmidia[0])
        else:
            self.tipo_item_var.configure(values=self.itens_proximaparada)
            self.tipo_item_var.set(self.itens_proximaparada[0])

    # --- Ações de UI ---
    def ao_sair_do_id(self, event=None):
        id_digitado = self.id_entry.get().strip().upper()
        if not id_digitado: return
        
        dados = self.service.consultar_endereco(id_digitado)
        
        self.endereco_entry.delete(0, ctk.END)
        self.numero_entry.delete(0, ctk.END)
        self.bairro_entry.delete(0, ctk.END)
        self.complemento_entry.delete(0, ctk.END)

        if dados:
            self.endereco_entry.insert(0, dados.get("endereco", ""))
            self.numero_entry.insert(0, dados.get("numero", ""))
            self.bairro_entry.insert(0, dados.get("bairro", ""))
            self.complemento_entry.insert(0, dados.get("complemento", ""))

    def adicionar_descricao(self):
        id_texto = self.id_entry.get().strip().upper()
        if not id_texto:
            messagebox.showerror("Atenção", "Digite o ID do Ponto primeiro.")
            return
            
        endereco = self.endereco_entry.get().upper()
        numero = self.numero_entry.get().upper()
        bairro = self.bairro_entry.get().upper()
        
        if not endereco or not numero or not bairro:
            messagebox.showerror("Atenção", "Preencha Logradouro, Número e Bairro.")
            return

        tipo_os = self.tipo_os_var.get().upper()
        tipo_item = self.tipo_item_var.get().upper()
        complemento = self.complemento_entry.get().upper()

        endereco_formatado = f"{endereco}, Nº {numero} - BAIRRO {bairro}"
        if complemento: endereco_formatado += f" - {complemento}"
        
        descricao = f"{tipo_os} DE {tipo_item} NA {endereco_formatado}, CONFORME DESCRIÇÃO DO CROQUI EM ANEXO.".upper()
        
        self.descricoes_acumuladas.append({"id": id_texto, "descricao": descricao})
        self._renderizar_tabela()

    def _renderizar_tabela(self):
        for widget in self.tabela_frame.winfo_children():
            widget.destroy()
            
        for idx, item in enumerate(self.descricoes_acumuladas):
            linha = ctk.CTkFrame(self.tabela_frame, fg_color="white", corner_radius=6)
            linha.pack(fill="x", pady=2)
            
            ctk.CTkLabel(linha, text=f"ID: {item['id']}", font=("Arial Bold", 13), width=80, text_color="#0F8C75").pack(side="left", padx=10)
            ctk.CTkLabel(linha, text=item["descricao"], font=("Arial", 12), justify="left", wraplength=600).pack(side="left", fill="x", expand=True, padx=10, pady=5)
            
            btn_excluir = ctk.CTkButton(linha, text="X", width=30, fg_color="transparent", hover_color="#FFE0E0", text_color="red", font=("Arial Bold", 14), command=lambda i=idx: self.excluir_da_tabela(i))
            btn_excluir.pack(side="right", padx=10)

    def excluir_da_tabela(self, index):
        if 0 <= index < len(self.descricoes_acumuladas):
            del self.descricoes_acumuladas[index]
            self._renderizar_tabela()

    def acao_criar_os(self):
        id_digitado = self.id_entry.get().strip().upper()
        if not id_digitado and not self.descricoes_acumuladas:
            messagebox.showerror("Erro", "Formulário vazio.")
            return

        # 1. Alerta de Histórico (Regra de Negócio que envolve UI)
        if id_digitado:
             resposta = messagebox.askyesno("Verificação de ID", f"Você já consultou o histórico do ID {id_digitado}?\nSe não, clique em NÃO para ver agora.")
             if not resposta:
                 historico = self.service.obter_historico_formatado(id_digitado)
                 messagebox.showinfo(f"Histórico ID {id_digitado}", historico)
                 return

        # 2. Coleta de dados
        form_dados = {
            'endereco': self.endereco_entry.get().upper(),
            'numero': self.numero_entry.get().upper(),
            'bairro': self.bairro_entry.get().upper(),
            'complemento': self.complemento_entry.get().upper()
        }
        
        modelo = "dados/modelo_etufor_urbmidia.docx" if self.pasta_escolhida_var.get() == "URBMIDIA" else "dados/modelo_etufor_prxparada.docx"

        # 3. Chama o Service
        sucesso, mensagem = self.service.processar_criacao_os(
            descricoes_acumuladas=self.descricoes_acumuladas,
            pasta_escolhida=self.pasta_escolhida_var.get(),
            modelo_escolhido=modelo,
            tipo_os=self.tipo_os_var.get(),
            tipo_item=self.tipo_item_var.get(),
            form_dados=form_dados,
            usuario_logado=self.usuario_logado
        )

        # 4. Trata o Resultado
        if sucesso:
            messagebox.showinfo("OS Gerada com Sucesso!", mensagem)
            # Limpeza geral
            self.id_entry.delete(0, ctk.END)
            self.endereco_entry.delete(0, ctk.END)
            self.numero_entry.delete(0, ctk.END)
            self.bairro_entry.delete(0, ctk.END)
            self.complemento_entry.delete(0, ctk.END)
            self.descricoes_acumuladas.clear()
            self._renderizar_tabela()
        else:
            messagebox.showerror("Erro ao Gerar OS", mensagem)

# Ponto de entrada para o main.py
def renderizar(frame_destino, usuario_logado):
    return OSView(master=frame_destino, usuario_logado=usuario_logado)