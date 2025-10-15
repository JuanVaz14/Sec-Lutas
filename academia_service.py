from models import Academia, Session
from sqlalchemy.exc import IntegrityError, NoResultFound
from typing import List

# --- C: CREATE (Cadastrar Nova Academia/Polo) ---
def cadastrar_academia(nome: str, endereco: str, responsavel: str) -> Academia | None:
    """Cadastra um novo polo/academia no banco de dados."""
    session = Session()
    try:
        # Verifica se já existe uma academia com o mesmo nome
        if session.query(Academia).filter_by(nome=nome).first():
            print(f"ERRO: Academia com o nome '{nome}' já está cadastrada.")
            return None
        
        nova_academia = Academia(
            nome=nome,
            endereco=endereco,
            responsavel=responsavel
        )
        
        session.add(nova_academia)
        session.commit()
        print(f"SUCESSO: Academia '{nome}' cadastrada com ID: {nova_academia.id}")
        return nova_academia
    
    except IntegrityError:
        print("ERRO: Ocorreu um erro de integridade ao cadastrar a academia.")
        session.rollback()
        return None
    finally:
        session.close()

# --- R: READ (Buscar e Listar Academias) ---
def buscar_academia_por_id(academia_id: int) -> Academia | None:
    """Busca uma academia específica pelo ID."""
    session = Session()
    try:
        academia = session.query(Academia).get(academia_id)
        return academia
    finally:
        session.close()

def listar_todas_academias() -> List[Academia]:
    """Lista todas as academias cadastradas."""
    session = Session()
    try:
        academias = session.query(Academia).all()
        return academias
    finally:
        session.close()

# --- U: UPDATE (Atualizar Informações) ---
def atualizar_academia(academia_id: int, endereco: str = None, responsavel: str = None) -> bool:
    """Atualiza o endereço e/ou responsável de uma academia pelo ID."""
    session = Session()
    try:
        academia = session.query(Academia).filter_by(id=academia_id).one()
        
        if endereco:
            academia.endereco = endereco
        if responsavel:
            academia.responsavel = responsavel
            
        session.commit()
        print(f"SUCESSO: Academia '{academia.nome}' (ID: {academia_id}) atualizada.")
        return True
    except NoResultFound:
        print(f"ERRO: Academia com ID {academia_id} não encontrada.")
        session.rollback()
        return False
    finally:
        session.close()
        
# --- D: DELETE (Remover Academia/Polo) ---
def deletar_academia(academia_id: int) -> bool:
    """Remove uma academia permanentemente pelo ID."""
    session = Session()
    try:
        academia = session.query(Academia).filter_by(id=academia_id).one()
        nome = academia.nome
        
        # IMPORTANTE: Se esta academia tiver alunos ou treinadores vinculados,
        # o banco de dados (SQLite por padrão) pode impedir a deleção
        # por conta da Chave Estrangeira.
        
        session.delete(academia)
        session.commit()
        print(f"SUCESSO: Academia '{nome}' removida permanentemente do cadastro.")
        return True
    except NoResultFound:
        print(f"ERRO: Academia com ID {academia_id} não encontrada para deleção.")
        session.rollback()
        return False
    except IntegrityError:
        print(f"ERRO: A academia '{nome}' possui alunos ou treinadores vinculados e não pode ser deletada.")
        session.rollback()
        return False
    finally:
        session.close()