from models import Aluno, Modalidade, MatriculaModalidade, Session
from sqlalchemy.exc import IntegrityError, NoResultFound
from typing import List
from datetime import date

# --- C: CREATE (Matricular Aluno em Modalidade) ---
def matricular_aluno(aluno_id: int, modalidade_id: int, numero_matricula: str, graduacao_inicial: str = "Iniciante") -> MatriculaModalidade | None:
    """Registra a matrícula de um aluno em uma modalidade específica."""
    session = Session()
    try:
        # 1. Checa se o aluno e modalidade existem (opcional, mas bom para feedback)
        aluno = session.query(Aluno).get(aluno_id)
        modalidade = session.query(Modalidade).get(modalidade_id)
        
        if not aluno or not modalidade:
            print("ERRO: Aluno ou Modalidade não encontrados.")
            return None

        # 2. Cria o novo registro de matrícula
        nova_matricula = MatriculaModalidade(
            aluno_id=aluno_id,
            modalidade_id=modalidade_id,
            numero_matricula=numero_matricula,
            data_inicio=date.today(), # Data de hoje como padrão para o início
            graduacao=graduacao_inicial
        )
        
        session.add(nova_matricula)
        session.commit()
        print(f"SUCESSO: Aluno '{aluno.nome_completo}' matriculado em {modalidade.nome}.")
        print(f"   Matrícula: {numero_matricula}, Graduação Inicial: {graduacao_inicial}")
        return nova_matricula
    
    except IntegrityError as e:
        # Captura erro se o número de matrícula já existir ou a unicidade de aluno_id/modalidade_id for violada
        if 'UNIQUE constraint failed: matriculas_modalidades.numero_matricula' in str(e):
             print(f"ERRO: Número de matrícula '{numero_matricula}' já existe.")
        elif '_aluno_modalidade_uc' in str(e):
             print(f"ERRO: Aluno já está matriculado nesta modalidade.")
        else:
            print("ERRO: Falha de integridade ao matricular. Verifique as IDs.")
            
        session.rollback()
        return None
    finally:
        session.close()

# --- R: READ (Buscar e Listar) ---
def listar_matriculas_aluno(aluno_id: int) -> List[MatriculaModalidade]:
    """Lista todas as modalidades em que um aluno está matriculado."""
    session = Session()
    try:
        matriculas = session.query(MatriculaModalidade).filter_by(aluno_id=aluno_id).all()
        return matriculas
    finally:
        session.close()

def listar_alunos_por_graduacao(modalidade_id: int, graduacao: str) -> List[MatriculaModalidade]:
    """Lista todos os alunos em uma modalidade com uma graduação específica (ex: Faixa Branca)."""
    session = Session()
    try:
        matriculas = session.query(MatriculaModalidade).filter(
            MatriculaModalidade.modalidade_id == modalidade_id,
            MatriculaModalidade.graduacao == graduacao
        ).all()
        return matriculas
    finally:
        session.close()

# --- U: UPDATE (Atualizar Graduação) ---
def atualizar_graduacao(aluno_id: int, modalidade_id: int, nova_graduacao: str) -> bool:
    """Atualiza a graduação/faixa de um aluno em uma modalidade específica."""
    session = Session()
    try:
        # Busca o registro específico usando a combinação única (aluno_id e modalidade_id)
        matricula = session.query(MatriculaModalidade).filter(
            MatriculaModalidade.aluno_id == aluno_id,
            MatriculaModalidade.modalidade_id == modalidade_id
        ).one()
        
        matricula.graduacao = nova_graduacao
        session.commit()
        
        # Para feedback amigável
        aluno = session.query(Aluno).get(aluno_id)
        modalidade = session.query(Modalidade).get(modalidade_id)
        
        print(f"SUCESSO: Graduação de '{aluno.nome_completo}' em {modalidade.nome} atualizada para {nova_graduacao}.")
        return True
        
    except NoResultFound:
        print("ERRO: Matrícula não encontrada. Verifique as IDs do aluno e modalidade.")
        session.rollback()
        return False
    finally:
        session.close()