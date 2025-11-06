# matricula_service.py

from typing import List, Optional
from sqlalchemy.exc import IntegrityError
from models import Aluno, Modalidade, Matricula, Session 
from datetime import date

# ==============================================================================
# OPERAÇÕES CRUD DE MATRÍCULAS
# ==============================================================================

# -----------------
# C: CREATE (MATRICULAR)
# -----------------

def matricular_aluno(aluno_id: int, modalidade_id: int, graduacao: str) -> bool:
    """Cria uma matrícula definindo numero_matricula como o ID do aluno."""
    session = Session()
    try:
        # Verifica existência de aluno e modalidade
        aluno = session.query(Aluno).filter_by(id=aluno_id).one_or_none()
        modalidade = session.query(Modalidade).filter_by(id=modalidade_id).one_or_none()
        if not aluno or not modalidade:
            return False

        numero_matricula = str(aluno_id)  # conforme solicitado: matrícula = ID do aluno

        nova = Matricula(
            numero_matricula=numero_matricula,
            graduacao=graduacao,
            aluno_id=aluno_id,
            modalidade_id=modalidade_id
        )
        session.add(nova)
        session.commit()
        return True
    except IntegrityError:
        session.rollback()
        return False
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()

# -----------------
# R: READ (BUSCAR/LISTAR)
# -----------------

def listar_matriculas_aluno(aluno_id: int) -> List[Matricula]:
    session = Session()
    try:
        return session.query(Matricula).filter_by(aluno_id=aluno_id).all()
    finally:
        session.close()


# -----------------
# U: UPDATE (ATUALIZAR)
# -----------------

def atualizar_graduacao(aluno_id: int, modalidade_id: int, nova_graduacao: str) -> bool:
    session = Session()
    try:
        matricula = session.query(Matricula).filter_by(aluno_id=aluno_id, modalidade_id=modalidade_id).one_or_none()
        if not matricula:
            return False
        matricula.graduacao = nova_graduacao
        session.add(matricula)
        session.commit()
        return True
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()

# -----------------
# D: DELETE (REMOVER) - Função Simples
# -----------------

def remover_matricula(aluno_id: int, modalidade_id: int) -> bool:
    """Remove uma matrícula específica."""
    session = Session()
    try:
        matricula = session.query(Matricula).filter(
            Matricula.aluno_id == aluno_id,
            Matricula.modalidade_id == modalidade_id
        ).first()
        
        if matricula:
            session.delete(matricula)
            session.commit()
            print("SUCESSO: Matrícula removida.")
            return True
        else:
            print("ALERTA: Matrícula não encontrada.")
            return False
    except Exception as e:
        session.rollback()
        print(f"ERRO ao remover matrícula: {e}")
        return False
    finally:
        session.close()