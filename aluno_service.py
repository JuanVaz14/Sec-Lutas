# aluno_service.py

from typing import List, Optional
from sqlalchemy.exc import IntegrityError
from models import Aluno, Session
from datetime import date

def cadastrar_aluno(nome_completo: str, cpf_limpo: str, academia_id: int,
                    graduacao: str = "", responsavel: str = "", telefone: str = "") -> Optional[int]:
    """Cadastra um aluno e retorna o id do aluno criado, ou None em caso de erro."""
    session = Session()
    try:
        cpf_formatado = f"{cpf_limpo[0:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:11]}"
        novo = Aluno(
            nome_completo=nome_completo,
            cpf_formatado=cpf_formatado,
            cpf_limpo=cpf_limpo,
            data_cadastro=date.today(),
            academia_id=academia_id,
            graduacao=graduacao,
            responsavel=responsavel,
            telefone=telefone,
            status_ativo=True
        )
        session.add(novo)
        session.commit()
        session.refresh(novo)
        return novo.id
    except IntegrityError:
        session.rollback()
        return None
    finally:
        session.close()

def buscar_aluno_por_cpf(cpf_limpo: str) -> Optional[Aluno]:
    session = Session()
    try:
        return session.query(Aluno).filter_by(cpf_limpo=cpf_limpo).one_or_none()
    finally:
        session.close()

def buscar_aluno_por_id(aluno_id: int) -> Optional[Aluno]:
    session = Session()
    try:
        return session.query(Aluno).filter_by(id=aluno_id).one_or_none()
    finally:
        session.close()

def listar_alunos_por_academia(academia_id: int) -> List[Aluno]:
    session = Session()
    try:
        return session.query(Aluno).filter_by(academia_id=academia_id).all()
    finally:
        session.close()

def listar_todos_alunos() -> List[Aluno]:
    session = Session()
    try:
        return session.query(Aluno).order_by(Aluno.nome_completo).all()
    finally:
        session.close()

def atualizar_status_aluno(aluno_id: int, ativo: bool) -> bool:
    session = Session()
    try:
        aluno = session.query(Aluno).filter_by(id=aluno_id).one_or_none()
        if not aluno:
            return False
        aluno.status_ativo = ativo
        session.add(aluno)
        session.commit()
        return True
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()

def deletar_aluno(aluno_id: int) -> bool:
    session = Session()
    try:
        aluno = session.query(Aluno).filter_by(id=aluno_id).one_or_none()
        if not aluno:
            return False
        session.delete(aluno)
        session.commit()
        return True
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()
