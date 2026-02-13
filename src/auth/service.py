import bcrypt
import smtplib
import random
import json
import os
from email.mime.text import MIMEText
from datetime import datetime
from config.database import get_db_connection

class AuthService:
    def __init__(self):
        self.caminho_login_salvo = "login_salvo.json"
        self.codigo_recuperacao = None
        self.email_recuperacao = None

    def cadastrar_usuario(self, username, email, senha, conf_senha):
        if not all([username, email, senha, conf_senha]):
            return False, "Preencha todos os campos."
        
        if senha != conf_senha:
            return False, "As senhas não coincidem."
        
        if len(senha) < 6:
            return False, "A senha deve ter no mínimo 6 caracteres."

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Verifica duplicidade
                    cursor.execute("SELECT id FROM sigp_login WHERE username = %s OR email = %s", (username, email))
                    if cursor.fetchone():
                        return False, "Usuário ou email já cadastrado."

                    # Hash da senha
                    senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

                    cursor.execute(
                        "INSERT INTO sigp_login (username, email, password_hash, tipo) VALUES (%s, %s, %s, %s)",
                        (username, email, senha_hash, "comum")
                    )
            return True, "Usuário cadastrado com sucesso."
        except Exception as e:
            return False, f"Erro no banco: {e}"

    def login(self, username, senha):
        if not username or not senha:
            return False, "Preencha usuário e senha.", None

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT password_hash, tipo, nome FROM sigp_login WHERE username = %s", (username,))
                    resultado = cursor.fetchone()

            if not resultado:
                return False, "Usuário não encontrado.", None

            senha_hash_banco, tipo_usuario, nome_completo = resultado

            if bcrypt.checkpw(senha.encode(), senha_hash_banco.encode()):
                usuario_data = {
                    "username": username,
                    "nome": nome_completo if nome_completo else username,
                    "is_admin": tipo_usuario == "admin"
                }
                return True, "Login realizado.", usuario_data
            else:
                return False, "Senha incorreta.", None

        except Exception as e:
            return False, f"Erro de conexão: {e}", None

# --- Funcionalidades de Recuperação de Senha ---
    def enviar_codigo_email(self, email):
        if not email:
            return False, "Digite o e-mail."

        # Verifica se email existe
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id FROM sigp_login WHERE email = %s", (email,))
                    if not cursor.fetchone():
                        return False, "E-mail não encontrado."
        except Exception as e:
            return False, f"Erro ao verificar email: {e}"

        # Gera e envia código
        codigo = str(random.randint(100000, 999999))
        self.codigo_recuperacao = codigo
        self.email_recuperacao = email
        
        remetente = os.getenv("EMAIL_REMETENTE")
        senha_app = os.getenv("EMAIL_SENHA")
        
        if not remetente or not senha_app:
            return False, "Configurações de e-mail não encontradas no .env"

        msg = MIMEText(f"Seu código de recuperação é: {codigo}")
        msg["Subject"] = "Recuperação de Senha - SIGP"
        msg["From"] = remetente
        msg["To"] = email

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(remetente, senha_app)
                server.sendmail(remetente, [email], msg.as_string())
            return True, "Código enviado com sucesso."
        except Exception as e:
            return False, f"Falha ao enviar e-mail: {e}"

    def verificar_codigo(self, codigo_digitado):
        if codigo_digitado == self.codigo_recuperacao:
            return True, "Código correto."
        return False, "Código incorreto."

    def redefinir_senha(self, nova_senha):
        if not nova_senha or len(nova_senha) < 6:
            return False, "Senha inválida (mínimo 6 caracteres)."
        
        try:
            senha_hash = bcrypt.hashpw(nova_senha.encode(), bcrypt.gensalt()).decode()
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE sigp_login SET password_hash = %s WHERE email = %s", 
                                   (senha_hash, self.email_recuperacao))
            return True, "Senha atualizada com sucesso."
        except Exception as e:
            return False, f"Erro ao atualizar senha: {e}"
        
# --- Persistência Local (Manter Conectado) ---
    def salvar_sessao_local(self, usuario_data):
        dados = {
            "usuario": usuario_data,
            "data_login": datetime.now().strftime("%Y-%m-%d")
        }
        with open(self.caminho_login_salvo, "w") as f:
            json.dump(dados, f)

    def ler_sessao_local(self):
        if os.path.exists(self.caminho_login_salvo):
            try:
                with open(self.caminho_login_salvo, "r") as f:
                    dados = json.load(f)
                
                # Verifica se é de hoje
                if dados.get("data_login") == datetime.now().strftime("%Y-%m-%d"):
                    return dados.get("usuario")
            except:
                pass # Se der erro lendo arquivo, ignora
            
            # Se chegou aqui, remove o arquivo inválido/antigo
            self.limpar_sessao_local()
        return None

    def limpar_sessao_local(self):
        if os.path.exists(self.caminho_login_salvo):
            os.remove(self.caminho_login_salvo)