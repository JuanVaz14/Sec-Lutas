# relatorio_service.py

from models import Academia, Aluno, Modalidade, Matricula, Session
from sqlalchemy import func
from typing import Dict, Any, List

def contar_alunos_por_academia() -> Dict[str, int]:
    """Retorna um dicionário com o nome da academia e a contagem total de alunos ativos."""
    session = Session()
    resultados = {}
    try:
        # Usa o SQLAlchemy para agrupar e contar os alunos por academia
        contagem = session.query(
            Academia.nome, 
            func.count(Aluno.id)
        ).join(Aluno).filter(
            Aluno.status_ativo == True  # Conta apenas alunos ativos
        ).group_by(Academia.nome).all()
        
        # Formata o resultado
        for nome_academia, total_alunos in contagem:
            resultados[nome_academia] = total_alunos
            
        return resultados
        
    except Exception as e:
        print(f"❌ ERRO ao gerar relatório de alunos por academia: {e}")
        return {}
    finally:
        session.close()

def contar_alunos_por_modalidade_e_graduacao() -> Dict[int, Dict[str, int]]:
    """
    Retorna um dicionário aninhado com contagem de alunos por modalidade e graduação.
    Formato: {modalidade_id: {graduacao: total_alunos}}
    """
    session = Session()
    resultados = {}
    try:
        # Busca todas as matrículas com alunos ativos
        contagem = session.query(
            Matricula.modalidade_id,
            Matricula.graduacao,
            func.count(Matricula.id)
        ).join(Aluno).filter(
            Aluno.status_ativo == True
        ).group_by(
            Matricula.modalidade_id,
            Matricula.graduacao
        ).all()
        
        # Organiza os resultados
        for modalidade_id, graduacao, total in contagem:
            if modalidade_id not in resultados:
                resultados[modalidade_id] = {}
            
            graduacao_str = graduacao if graduacao else "Não informada"
            resultados[modalidade_id][graduacao_str] = total
            
        return resultados
        
    except Exception as e:
        print(f"❌ ERRO ao gerar relatório de modalidades: {e}")
        return {}
    finally:
        session.close()

def listar_alunos_por_modalidade_e_graduacao(modalidade_nome: str, graduacao: str) -> List[Dict[str, str]]:
    """
    Lista alunos ativos em uma modalidade específica com uma dada graduação.
    Retorna uma lista de dicionários com nome do aluno e número de matrícula.
    """
    session = Session()
    resultados = []
    try:
        modalidade = session.query(Modalidade).filter_by(nome=modalidade_nome).first()
        if not modalidade:
            print(f"❌ ERRO: Modalidade '{modalidade_nome}' não encontrada.")
            return []

        # Faz a busca na tabela de associação
        matriculas = session.query(Matricula).join(Aluno).filter(
            Matricula.modalidade_id == modalidade.id,
            Matricula.graduacao == graduacao,
            Aluno.status_ativo == True
        ).all()
        
        # Formata o resultado
        for matricula in matriculas:
            resultados.append({
                "nome_aluno": matricula.aluno.nome_completo,
                "matricula": matricula.numero_matricula,
                "academia": matricula.aluno.academia.nome if matricula.aluno.academia else "N/A"
            })
            
        return resultados
        
    except Exception as e:
        print(f"❌ ERRO ao gerar relatório de graduação: {e}")
        return []
    finally:
        session.close()