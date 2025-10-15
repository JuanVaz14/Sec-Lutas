# relatorio_service.py

from models import Academia, Aluno, Modalidade, Session
from sqlalchemy import func
from typing import Dict, Any, List

def contar_alunos_por_academia() -> Dict[str, Any]:
    """Retorna um dicionário com o nome da academia e a contagem total de alunos ativos."""
    session = Session()
    resultados = {}
    try:
        # Usa o SQLAlchemy para agrupar e contar os alunos por academia
        contagem = session.query(
            Academia.nome, 
            func.count(Aluno.id)
        ).join(Aluno).filter(
            Aluno.status_ativo == True # Conta apenas alunos ativos
        ).group_by(Academia.nome).all()
        
        # Formata o resultado
        for nome_academia, total_alunos in contagem:
            resultados[nome_academia] = total_alunos
            
        return resultados
        
    except Exception as e:
        print(f"ERRO ao gerar relatório de alunos por academia: {e}")
        return {}
    finally:
        session.close()

def contar_alunos_por_modalidade_e_graduacao(modalidade_nome: str, graduacao: str) -> List[Dict[str, str]]:
    """
    Lista alunos ativos em uma modalidade específica com uma dada graduação.
    Retorna uma lista de dicionários com nome do aluno e número de matrícula.
    """
    from models import MatriculaModalidade # Importado aqui para evitar circularidade se models for complexo
    
    session = Session()
    resultados = []
    try:
        modalidade = session.query(Modalidade).filter_by(nome=modalidade_nome).first()
        if not modalidade:
            print(f"ERRO: Modalidade '{modalidade_nome}' não encontrada.")
            return []

        # Faz a busca na tabela de associação
        contagem = session.query(MatriculaModalidade).join(Aluno).filter(
            MatriculaModalidade.modalidade_id == modalidade.id,
            MatriculaModalidade.graduacao == graduacao,
            Aluno.status_ativo == True
        ).all()
        
        # Formata o resultado
        for matricula in contagem:
            resultados.append({
                "nome_aluno": matricula.aluno.nome_completo,
                "matricula": matricula.numero_matricula,
                "academia": matricula.aluno.academia.nome if matricula.aluno.academia else "N/A"
            })
            
        return resultados
        
    except Exception as e:
        print(f"ERRO ao gerar relatório de graduação: {e}")
        return []
    finally:
        session.close()