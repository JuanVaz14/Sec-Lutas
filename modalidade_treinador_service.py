# modalidade_treinador_service.py

from models import Modalidade, Treinador, Session
from sqlalchemy.exc import IntegrityError, NoResultFound
from typing import List

# --- C R U D - MODALIDADES ---

def cadastrar_modalidade(nome: str, tipo: str) -> Modalidade | None:
    """Cadastra uma nova modalidade (luta/esporte) no banco de dados."""
    session = Session()
    try:
        if session.query(Modalidade).filter_by(nome=nome).first():
            print(f"ERRO: Modalidade '{nome}' já está cadastrada.")
            return None
            
        nova_modalidade = Modalidade(nome=nome, tipo=tipo)
        session.add(nova_modalidade)
        session.commit()
        print(f"SUCESSO: Modalidade '{nome}' cadastrada. Tipo: {tipo}.")
        return nova_modalidade
    except IntegrityError:
        print("ERRO: Falha ao cadastrar modalidade.")
        session.rollback()
        return None
    finally:
        session.close()

def listar_modalidades() -> List[Modalidade]:
    """Lista todas as modalidades cadastradas."""
    session = Session()
    try:
        return session.query(Modalidade).all()
    finally:
        session.close()

# --- C R U D - TREINADORES ---

def cadastrar_treinador(nome: str, telefone: str, certificacao: str, academia_id: int, modalidade_id: int) -> Treinador | None:
    """Cadastra um novo treinador no banco de dados, associando-o à academia e modalidade."""
    session = Session()
    try:
        # A validação de FK é feita implicitamente. Se ID for inválida, IntegrityError ocorre.
        
        novo_treinador = Treinador(
            nome_completo=nome,
            telefone=telefone,
            certificacao=certificacao,
            academia_id=academia_id,
            modalidade_id=modalidade_id
        )
        
        session.add(novo_treinador)
        session.commit()
        
        # Para um print mais amigável
        modalidade = session.query(Modalidade).get(modalidade_id)
        
        print(f"SUCESSO: Treinador '{nome}' cadastrado para {modalidade.nome}.")
        return novo_treinador
    
    except IntegrityError:
        print("ERRO: Falha ao cadastrar treinador. Verifique se as IDs de Academia e Modalidade são válidas.")
        session.rollback()
        return None
    finally:
        session.close()


def listar_treinadores_por_modalidade(modalidade_id: int) -> List[Treinador]:
    """Lista todos os treinadores de uma determinada modalidade."""
    session = Session()
    try:
        treinadores = session.query(Treinador).filter_by(modalidade_id=modalidade_id).all()
        return treinadores
    finally:
        session.close()


def deletar_treinador(treinador_id: int) -> bool:
    """Remove um treinador permanentemente pelo ID."""
    session = Session()
    try:
        treinador = session.query(Treinador).filter_by(id=treinador_id).one()
        nome = treinador.nome_completo
        
        session.delete(treinador)
        session.commit()
        print(f"SUCESSO: Treinador '{nome}' removido.")
        return True
    except NoResultFound:
        print(f"ERRO: Treinador com ID {treinador_id} não encontrado para deleção.")
        session.rollback()
        return False
    finally:
        session.close()