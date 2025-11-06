# auth_service.py

from models import Usuario, Session
from sqlalchemy.exc import IntegrityError, NoResultFound
import bcrypt
from typing import List, Optional

# --- C R U D - USUÁRIOS ---

def registrar_usuario(nome_usuario: str, senha_plana: str, papel: str = "VIEWER") -> Optional[Usuario]:
    """Registra um novo usuário com senha criptografada e papel definido (padrão: VIEWER)."""
    session = Session()
    papel_upper = papel.upper()
    
    if papel_upper not in ["ADMIN", "EDITOR", "VIEWER"]:
        print("❌ ERRO: Papel inválido. Use ADMIN, EDITOR ou VIEWER.")
        return None
    
    try:
        if session.query(Usuario).filter_by(nome_usuario=nome_usuario).first():
            print("❌ ERRO: Nome de usuário já existe.")
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
        print(f"✅ SUCESSO: Usuário '{nome_usuario}' registrado com papel: {papel_upper}.")
        return novo_usuario
        
    except Exception as e:
        print(f"❌ ERRO ao registrar usuário: {e}")
        session.rollback()
        return None
    finally:
        session.close()

def autenticar_usuario(nome_usuario: str, senha_plana: str) -> Optional[Usuario]:
    """Retorna o objeto usuário autenticado ou None."""
    session = Session()
    try:
        usuario = session.query(Usuario).filter_by(nome_usuario=nome_usuario).first()
        if not usuario:
            return None
        
        senha_plana_bytes = senha_plana.encode('utf-8')
        senha_hash_bytes = usuario.senha_hash.encode('utf-8')
        
        if bcrypt.checkpw(senha_plana_bytes, senha_hash_bytes):
            print(f"✅ Login bem-sucedido para o usuário: {nome_usuario} ({usuario.papel})")
            return usuario
        else:
            return None
    except Exception as e:
        print(f"❌ ERRO durante a autenticação: {e}")
        return None
    finally:
        session.close()

def inicializar_usuario_admin():
    """Cria o primeiro usuário (juan) como ADMIN se nenhum existir."""
    session = Session()
    try:
        if session.query(Usuario).count() == 0:
            print("--- Criando o Primeiro Usuário (juan) como ADMIN ---")
            registrar_usuario("juan", "Lke74890@", papel="ADMIN")
    finally:
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
            print("❌ ERRO: Papel inválido. Use ADMIN, EDITOR ou VIEWER.")
            return False
            
        usuario.papel = novo_papel_upper
        session.commit()
        print(f"✅ SUCESSO: Papel do usuário '{nome_usuario}' atualizado para {novo_papel_upper}.")
        return True
        
    except NoResultFound:
        print(f"❌ ERRO: Usuário '{nome_usuario}' não encontrado.")
        return False
    except Exception as e:
        print(f"❌ ERRO ao atualizar papel: {e}")
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
                print("❌ ERRO: Não é possível deletar o último administrador do sistema.")
                return False
        
        session.delete(usuario)
        session.commit()
        print(f"✅ SUCESSO: Usuário '{nome_usuario}' deletado.")
        return True
        
    except NoResultFound:
        print(f"❌ ERRO: Usuário '{nome_usuario}' não encontrado.")
        return False
    except Exception as e:
        print(f"❌ ERRO ao deletar usuário: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def checar_permissao(usuario: Usuario, papel_necessario: str) -> bool:
    """Retorna True se o usuário tem o papel necessário.
    Usuário ADMIN tem acesso a tudo.
    Usuário EDITOR tem acesso a VIEWER também.
    """
    if usuario is None:
        return False
    
    papel_atual = (usuario.papel or "").upper()
    papel_necessario = (papel_necessario or "").upper()
    
    # ADMIN tem acesso total
    if papel_atual == "ADMIN":
        return True
    
    # EDITOR tem acesso a VIEWER também
    if papel_atual == "EDITOR" and papel_necessario in ["EDITOR", "VIEWER"]:
        return True
    
    # Caso contrário, precisa ser exatamente o papel necessário
    return papel_atual == papel_necessario