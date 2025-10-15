# auth_service.py

from models import Usuario, Session
from sqlalchemy.exc import IntegrityError, NoResultFound
import bcrypt
from typing import List

# --- C R U D - USUÁRIOS ---

def registrar_usuario(nome_usuario: str, senha_plana: str, papel: str = "VIEWER") -> Usuario | None:
    """Registra um novo usuário com senha criptografada e papel definido (padrão: VIEWER)."""
    session = Session()
    papel_upper = papel.upper()
    try:
        if session.query(Usuario).filter_by(nome_usuario=nome_usuario).first():
            print("ERRO: Nome de usuário já existe.")
            return None
        
        senha_bytes = senha_plana.encode('utf-8')
        senha_hash = bcrypt.hashpw(senha_bytes, bcrypt.gensalt())
        
        novo_usuario = Usuario(
            nome_usuario=nome_usuario,
            senha_hash=senha_hash.decode('utf-8'),
            papel=papel_upper
        )
        
        session.add(novo_usuario)
        session.commit()
        print(f"SUCESSO: Usuário '{nome_usuario}' registrado com papel: {papel_upper}.")
        return novo_usuario
        
    except Exception as e:
        print(f"ERRO ao registrar usuário: {e}")
        session.rollback()
        return None
    finally:
        session.close()

def autenticar_usuario(nome_usuario: str, senha_plana: str) -> bool:
    """Verifica se a senha fornecida corresponde ao hash armazenado."""
    session = Session()
    try:
        usuario = session.query(Usuario).filter_by(nome_usuario=nome_usuario).first()
        
        if not usuario:
            return False 
        
        senha_plana_bytes = senha_plana.encode('utf-8')
        senha_hash_bytes = usuario.senha_hash.encode('utf-8')
        
        if bcrypt.checkpw(senha_plana_bytes, senha_hash_bytes):
            print(f"Login bem-sucedido para o usuário: {nome_usuario} ({usuario.papel})")
            return True
        else:
            return False 
            
    except Exception as e:
        print(f"ERRO durante a autenticação: {e}")
        return False
    finally:
        session.close()

def inicializar_usuario_admin():
    """Cria o primeiro usuário (juan) como ADMIN se nenhum existir."""
    session = Session()
    if session.query(Usuario).count() == 0:
        print("--- Criando o Primeiro Usuário (juan) como ADMIN ---")
        # Usuário: juan / Senha: Lke74890@
        registrar_usuario("juan", "Lke74890@", papel="ADMIN") 
    session.close()


def listar_usuarios() -> List[Usuario]:
    """Lista todos os usuários e seus papéis."""
    session = Session()
    try:
        return session.query(Usuario).all()
    finally:
        session.close()


def atualizar_papel_usuario(nome_usuario: str, novo_papel: str) -> bool:
    """Atualiza o nível de acesso (papel) de um usuário existente."""
    session = Session()
    try:
        usuario = session.query(Usuario).filter_by(nome_usuario=nome_usuario).one()
        novo_papel_upper = novo_papel.upper()
        
        if novo_papel_upper not in ["ADMIN", "EDITOR", "VIEWER"]:
             print("ERRO: Papel inválido. Use ADMIN, EDITOR ou VIEWER.")
             return False
             
        usuario.papel = novo_papel_upper
        session.commit()
        print(f"SUCESSO: Papel do usuário '{nome_usuario}' atualizado para {novo_papel_upper}.")
        return True
        
    except NoResultFound:
        print(f"ERRO: Usuário '{nome_usuario}' não encontrado.")
        return False
    except Exception as e:
        print(f"ERRO ao atualizar papel: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def deletar_usuario(nome_usuario: str) -> bool:
    """Deleta um usuário permanentemente, com checagem de segurança."""
    session = Session()
    try:
        usuario = session.query(Usuario).filter_by(nome_usuario=nome_usuario).one()
        
        # Checagem de segurança: Não permita deletar se ele for o último ADMIN
        if usuario.papel == "ADMIN":
            admin_count = session.query(Usuario).filter_by(papel="ADMIN").count()
            if admin_count <= 1:
                print("ERRO: Não é possível deletar o último administrador do sistema.")
                return False
        
        session.delete(usuario)
        session.commit()
        print(f"SUCESSO: Usuário '{nome_usuario}' deletado.")
        return True
        
    except NoResultFound:
        print(f"ERRO: Usuário '{nome_usuario}' não encontrado.")
        return False
    except Exception as e:
        print(f"ERRO ao deletar usuário: {e}")
        session.rollback()
        return False
    finally:
        session.close()


# --- CHECAGEM DE PERMISSÃO (FLASK) ---

def checar_permissao(nome_usuario: str, papeis_permitidos: list) -> bool:
    """Verifica se o usuário logado tem um papel permitido para a ação."""
    session = Session()
    try:
        usuario = session.query(Usuario).filter_by(nome_usuario=nome_usuario).one()
        # Converte o papel do usuário para maiúsculas e checa se está na lista permitida
        return usuario.papel in [p.upper() for p in papeis_permitidos]
    except NoResultFound:
        return False
    finally:
        session.close()