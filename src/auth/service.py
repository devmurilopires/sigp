import bcrypt
from email.mime.text import MIMEText
from datetime import datetime
from config.database import get_db_connection  # Nossa nova conexão otimizada

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