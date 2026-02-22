import customtkinter as ctk
from PIL import Image

from src.auth.view import LoginView
from src.auth.service import AuthService
from src.ordem_servico.view import renderizar as renderizar_os

try:
    from utils import resource_path
except ImportError:
    def resource_path(path): return path

COLOR_PRIMARY = "#0F8C75"
COLOR_PRIMARY_HOVER = "#0B6B59"
COLOR_BG = "#F2F2F2"

def iniciar_sistema(usuario_dados):
    nome_usuario = usuario_dados.get("nome", "Usuário")
    is_admin = usuario_dados.get("is_admin", False)

    app = ctk.CTk()
    app.title("SIGP - Sistema Integrado de Gerenciamento e Produtividade")
    app.configure(fg_color=COLOR_BG)
    
    try:
        app.state("zoomed") 
        app.iconbitmap(resource_path("assets/sigp_logo.ico"))
    except:
        app.geometry("1280x720")

    # TOPO
    frame_topo = ctk.CTkFrame(app, height=70, corner_radius=0)
    frame_topo.pack(fill="x")

    try:
        caminho_logo = resource_path("assets/sigp_logo.png")
        img_logo = ctk.CTkImage(Image.open(caminho_logo), size=(100, 100))
        ctk.CTkLabel(frame_topo, image=img_logo, text="").pack(side="left", padx=(20, 10))
    except:
        ctk.CTkLabel(frame_topo, text="SIGP", font=("Arial Black", 24), text_color=COLOR_PRIMARY).pack(side="left", padx=(20, 10))

    ctk.CTkLabel(frame_topo, text="Sistema Integrado de Gerenciamento e Produtividade", font=("Century Gothic bold", 20)).pack(side="left")

    perfil_texto = f"👤 Olá, {nome_usuario} ({'Admin' if is_admin else 'Comum'})"
    ctk.CTkLabel(frame_topo, text=perfil_texto, font=("Arial", 14), text_color="gray").pack(side="right", padx=20)

    # MENU
    menu_container = ctk.CTkFrame(app, fg_color="transparent")
    menu_container.pack(fill="x", padx=10, pady=(15, 0))

    menu_botoes = [
        ("Ordem de Serviço", COLOR_PRIMARY),
        ("Gráficos", COLOR_PRIMARY),
        ("Relatórios OS", COLOR_PRIMARY),
        ("Parecer Técnico", COLOR_PRIMARY),
        ("Relatórios Parecer", COLOR_PRIMARY),
        ("Histórico", COLOR_PRIMARY),
    ]
    if is_admin: menu_botoes.append(("Cadastro de Endereço", "#14A1D9"))

    # CONTEÚDO
    frame_conteudo = ctk.CTkFrame(app, fg_color="#FFFFFF", corner_radius=15)
    frame_conteudo.pack(fill="both", expand=True, padx=20, pady=20)

    abas = {}

    def criar_placeholder(parent_frame, titulo_modulo):
        container = ctk.CTkFrame(parent_frame, fg_color="transparent")
        container.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(container, text="🚧", font=("Arial", 50)).pack(pady=10)
        ctk.CTkLabel(container, text=titulo_modulo, font=("Arial Black", 24), text_color=COLOR_PRIMARY).pack(pady=5)
        ctk.CTkLabel(container, text="Módulo em refatoração para a nova arquitetura.", font=("Arial", 15), text_color="gray").pack()

    for nome, _ in menu_botoes:
        aba = ctk.CTkFrame(frame_conteudo, fg_color="transparent")
        abas[nome] = aba

    renderizar_os(abas["Ordem de Serviço"], nome_usuario)

    criar_placeholder(abas["Gráficos"], "Dashboard e Gráficos")
    criar_placeholder(abas["Relatórios OS"], "Relatórios de OS")
    criar_placeholder(abas["Parecer Técnico"], "Geração de Parecer Técnico")
    criar_placeholder(abas["Relatórios Parecer"], "Relatórios de Pareceres")
    criar_placeholder(abas["Histórico"], "Lixeira e Histórico")
    if is_admin: criar_placeholder(abas["Cadastro de Endereço"], "Cadastro de Endereços")

    def selecionar_aba(nome_aba):
        for aba in abas.values(): aba.pack_forget()
        abas[nome_aba].pack(fill="both", expand=True)

    for texto, cor in menu_botoes:
        btn = ctk.CTkButton(menu_container, text=texto, fg_color=cor, font=("Arial Bold", 13), corner_radius=8, height=35, hover_color=COLOR_PRIMARY_HOVER, command=lambda t=texto: selecionar_aba(t))
        btn.pack(side="left", padx=5)

    selecionar_aba("Ordem de Serviço")
    app.mainloop()

def bootstrap():
    """O ponto de entrada real. Verifica a sessão ANTES de abrir a janela."""
    auth = AuthService()
    sessao = auth.ler_sessao()
    
    # Se já tem sessão, pula o login e abre o sistema direto
    if sessao:
        iniciar_sistema(sessao)
    else:
        # Se não tem sessão, abre a janela de login
        def on_login_sucesso(dados_usuario):
            app_login.destroy()
            iniciar_sistema(dados_usuario)

        app_login = LoginView(on_login_success=on_login_sucesso)
        app_login.mainloop()

if __name__ == "__main__":
    bootstrap()