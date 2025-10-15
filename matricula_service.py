# matricula_service.py

from models import Aluno, Modalidade, Matricula, Session 
from sqlalchemy.exc import IntegrityError
from datetime import date

# ==============================================================================
# OPERAÇÕES CRUD DE MATRÍCULAS
# ==============================================================================

# -----------------
# C: CREATE (MATRICULAR)
# -----------------

def matricular_aluno(aluno_id: int, modalidade_id: int, numero_matricula: str, graduacao_inicial: str) -> Matricula | None:
    """Matricula um aluno em uma modalidade específica."""
    session = Session()
    try:
        # 1. Validação: Checa se Aluno e Modalidade existem
        aluno = session.get(Aluno, aluno_id)
        modalidade = session.get(Modalidade, modalidade_id)
        
        if not aluno:
            print(f"ERRO: Aluno com ID {aluno_id} não encontrado.")
            return None
        if not modalidade:
            print(f"ERRO: Modalidade com ID {modalidade_id} não encontrada.")
            return None

        # 2. Checa se o aluno já está matriculado nesta modalidade
        matricula_existente = session.query(Matricula).filter(
            Matricula.aluno_id == aluno_id,
            Matricula.modalidade_id == modalidade_id
        ).first()
        
        if matricula_existente:
            print(f"ALERTA: O aluno {aluno.nome_completo} já está matriculado na modalidade {modalidade.nome}.")
            return None

        # 3. Cria a nova Matrícula
        nova_matricula = Matricula(
            aluno_id=aluno_id,
            modalidade_id=modalidade_id,
            numero_matricula=numero_matricula,
            graduacao=graduacao_inicial,
            data_matricula=date.today()
        )
        
        session.add(nova_matricula)
        session.commit()
        print(f"SUCESSO: Matrícula {numero_matricula} criada para {aluno.nome_completo} em {modalidade.nome}.")
        return nova_matricula

    except IntegrityError:
        session.rollback()
        print("ERRO: O número de matrícula informado já existe.")
        return None
    except Exception as e:
        session.rollback()
        print(f"ERRO ao matricular aluno: {e}")
        return None
    finally:
        session.close()

# -----------------
# R: READ (BUSCAR/LISTAR)
# -----------------

def listar_matriculas_aluno(aluno_id: int) -> list[Matricula]:
    """Lista todas as matrículas de um aluno específico."""
    session = Session()
    try:
        # Carrega a modalidade junto para evitar erro de Lazy Loading no main.py
        matriculas = session.query(Matricula).filter(Matricula.aluno_id == aluno_id).all()
        return matriculas
    except Exception as e:
        print(f"ERRO ao listar matrículas do aluno {aluno_id}: {e}")
        return []
    finally:
        session.close()


# -----------------
# U: UPDATE (ATUALIZAR)
# -----------------

def atualizar_graduacao(aluno_id: int, modalidade_id: int, nova_graduacao: str) -> bool:
    """Atualiza a graduação (faixa/nível) de uma matrícula existente."""
    session = Session()
    try:
        matricula = session.query(Matricula).filter(
            Matricula.aluno_id == aluno_id,
            Matricula.modalidade_id == modalidade_id
        ).first()
        
        if matricula:
            nome_aluno = session.get(Aluno, aluno_id).nome_completo # Busca nome para feedback
            nome_modalidade = session.get(Modalidade, modalidade_id).nome # Busca modalidade para feedback

            matricula.graduacao = nova_graduacao
            session.commit()
            print(f"SUCESSO: Graduação de {nome_aluno} em {nome_modalidade} atualizada para '{nova_graduacao}'.")
            return True
        else:
            print("ALERTA: Matrícula não encontrada para o aluno/modalidade especificados.")
            return False
            
    except Exception as e:
        session.rollback()
        print(f"ERRO ao atualizar graduação: {e}")
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