import customtkinter as ctk
from PIL import Image

from src.auth.view import LoginView
from src.auth.service import AuthService
from src.ordem_servico.view import renderizar as renderizar_os
from src.parecer.view import renderizar as renderizar_parecer
from src.relatorios.view import renderizar as renderizar_relatorios
from src.historico.view import renderizar as renderizar_historico
from src.dashboard.view import renderizar as renderizar_dashboard
from src.enderecos.view import renderizar as renderizar_enderecos

try:
    from src.shared.utils import resource_path
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
    
    # Tenta forçar tela cheia logo de cara
    try:
        app.state("zoomed") 
        app.iconbitmap(resource_path("assets/sigp_logo.ico"))
    except:
        app.geometry("1280x720")

    # =====================================================================
    # 1. TELA DE CARREGAMENTO (SPLASH SCREEN)
    # =====================================================================
    tela_carregamento = ctk.CTkFrame(app, fg_color=COLOR_BG)
    tela_carregamento.pack(fill="both", expand=True)
    
    # Tenta carregar a sua logo para a tela de espera, se não achar, põe texto
    try:
        caminho_logo = resource_path("assets/sigp_logo.png")
        img_logo_splash = ctk.CTkImage(Image.open(caminho_logo), size=(350, 350))
        ctk.CTkLabel(tela_carregamento, image=img_logo_splash, text="").pack(expand=True, pady=(150, 10))
    except:
        ctk.CTkLabel(tela_carregamento, text="SIGP", font=("Arial Black", 120), text_color=COLOR_PRIMARY).pack(expand=True, pady=(150, 10))
        
    ctk.CTkLabel(tela_carregamento, text="Carregando módulos e painéis do sistema...\nPor favor, aguarde. ⏳", font=("Arial Bold", 23), text_color="#555", justify="center").pack(expand=True, pady=(0, 150))
    
    # MÁGICA: Força o Windows a pintar a tela de aguarde AGORA, antes de travar processando
    app.update()

    # =====================================================================
    # 2. MONTAGEM DA INTERFACE PRINCIPAL (Escondida dentro do frame_principal)
    # =====================================================================
    frame_principal = ctk.CTkFrame(app, fg_color="transparent")
    
    # TOPO
    frame_topo = ctk.CTkFrame(frame_principal, height=85, corner_radius=0)
    frame_topo.pack(fill="x")

    try:
        caminho_logo = resource_path("assets/sigp_logo.png")
        # Dei uma leve ajustada no tamanho da logo (90x90) para o cabeçalho respirar melhor
        img_logo = ctk.CTkImage(Image.open(caminho_logo), size=(90, 90))
        ctk.CTkLabel(frame_topo, image=img_logo, text="").pack(side="left", padx=(20, 10), pady=5)
    except:
        ctk.CTkLabel(frame_topo, text="SIGP", font=("Arial Black", 24), text_color=COLOR_PRIMARY).pack(side="left", padx=(20, 10))

    # O segredo do alinhamento está aqui no 'pady=(12, 0)', que empurra o texto um pouco para baixo
    ctk.CTkLabel(frame_topo, text="Sistema Integrado de Gerenciamento e Produtividade", font=("Century Gothic bold", 20)).pack(side="left", pady=(12, 0))

    perfil_texto = f"👤 Olá, {nome_usuario} ({'Admin' if is_admin else 'Comum'})"
    ctk.CTkLabel(frame_topo, text=perfil_texto, font=("Arial", 14), text_color="gray").pack(side="right", padx=20)

    # MENU
    menu_container = ctk.CTkFrame(frame_principal, fg_color="transparent")
    menu_container.pack(fill="x", padx=10, pady=(15, 0))

    menu_botoes = [
        ("Gráficos", COLOR_PRIMARY),
        ("Ordem de Serviço", COLOR_PRIMARY),
        ("Relatórios OS", COLOR_PRIMARY),
        ("Parecer Técnico", COLOR_PRIMARY),
        ("Relatórios Parecer", COLOR_PRIMARY),
        ("Histórico", COLOR_PRIMARY),
    ]
    if is_admin: menu_botoes.append(("Cadastro de Endereço", "#F24822"))

    # CONTEÚDO
    frame_conteudo = ctk.CTkFrame(frame_principal, fg_color="#FFFFFF", corner_radius=15)
    frame_conteudo.pack(fill="both", expand=True, padx=20, pady=20)

    abas = {}

    for nome, _ in menu_botoes:
        aba = ctk.CTkFrame(frame_conteudo, fg_color="transparent")
        abas[nome] = aba

    # --- PROCESSAMENTO PESADO QUE TRAVAVA A TELA ---
    renderizar_os(abas["Ordem de Serviço"], usuario_dados)
    renderizar_dashboard(abas["Gráficos"], usuario_dados)
    renderizar_relatorios(abas["Relatórios OS"], usuario_dados, tipo="OS")
    renderizar_parecer(abas["Parecer Técnico"], usuario_dados)
    renderizar_relatorios(abas["Relatórios Parecer"], usuario_dados, tipo="PARECER")
    renderizar_historico(abas["Histórico"], usuario_dados)
    if is_admin: renderizar_enderecos(abas["Cadastro de Endereço"], usuario_dados)

    def selecionar_aba(nome_aba):
        for aba in abas.values(): aba.pack_forget()
        abas[nome_aba].pack(fill="both", expand=True)

    for texto, cor in menu_botoes:
        btn = ctk.CTkButton(menu_container, text=texto, fg_color=cor, font=("Arial Bold", 13), corner_radius=8, height=35, hover_color=COLOR_PRIMARY_HOVER, command=lambda t=texto: selecionar_aba(t))
        btn.pack(side="left", padx=5)

    selecionar_aba("Ordem de Serviço")

    # =====================================================================
    # 3. FIM DO CARREGAMENTO - EXIBE O SISTEMA
    # =====================================================================
    # Apaga a tela de carregamento e mostra o sistema completo que montamos escondido
    tela_carregamento.destroy()
    frame_principal.pack(fill="both", expand=True)
    
    # Reforça a instrução de maximizar, caso o Windows tenha ignorado antes
    try:
        app.state("zoomed") 
    except:
        pass

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