# aluno_service.py

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, Session # <-- joinedload é necessário para Eager Loading!
from datetime import datetime
import re

# Importa as classes do models.py
from models import Aluno, Academia, Matricula, Modalidade, engine, Session 

# --- Funções Auxiliares ---

def limpar_cpf(cpf: str) -> str:
    """Remove pontuação e retorna o CPF como string de 11 dígitos."""
    if not isinstance(cpf, str):
        return ""
    return re.sub(r'[^0-9]', '', cpf).zfill(11)

# ==============================================================================
# OPERAÇÕES CRUD DE ALUNOS
# ==============================================================================

# -----------------
# C: CREATE (CADASTRAR) - CORRIGIDA PARA EVITAR DetachedInstanceError NO MAIN
# -----------------

def cadastrar_aluno(nome: str, data_nasc: str, cpf: str, academia_id: int) -> Aluno | None:
    """Cadastra um novo aluno no banco de dados."""
    session = Session()
    cpf_limpo = limpar_cpf(cpf)
    
    try:
        # 1. Validação de Dados
        data_nascimento = datetime.strptime(data_nasc, '%Y-%m-%d').date()
        
        # 2. Checa se o CPF já existe
        if session.query(Aluno).filter(Aluno.cpf_limpo == cpf_limpo).first():
            print(f"ALERTA: Já existe um aluno cadastrado com o CPF {cpf}.")
            return None
            
        # 3. Cria o novo objeto Aluno
        novo_aluno = Aluno(
            nome_completo=nome,
            data_nascimento=data_nascimento,
            cpf_formatado=cpf, # Salva o CPF com a formatação original
            cpf_limpo=cpf_limpo, # Salva o CPF limpo para buscas
            academia_id=academia_id, # Associa à academia
            status_ativo=True # Começa ativo
        )
        
        session.add(novo_aluno)
        session.commit()

        # >>>>>> CORREÇÃO CRÍTICA PARA DetachedInstanceError NO MAIN <<<<<<
        # Acessa os atributos ANTES de fechar a sessão. 
        # Isso garante que eles sejam carregados e 'cached' no objeto Aluno.
        # Caso contrário, ao tentar imprimir no main, ele tentará um 'refresh' 
        # e falhará, pois a sessão estará fechada.
        nome_cache = novo_aluno.nome_completo 
        cpf_cache = novo_aluno.cpf_formatado
        
        print(f"SUCESSO: Aluno '{nome_cache}' cadastrado. CPF: {cpf_cache}.")
        return novo_aluno

    except ValueError:
        session.rollback()
        print("ERRO: Formato de Data de Nascimento inválido. Use AAAA-MM-DD.")
        return None
    except IntegrityError:
        session.rollback()
        print("ERRO: Falha de integridade (possivelmente CPF duplicado ou ID de academia inválido).")
        return None
    except Exception as e:
        session.rollback()
        print(f"ERRO DESCONHECIDO ao cadastrar aluno: {e}")
        return None
    finally:
        session.close()

# -----------------
# R: READ (BUSCAR/LISTAR)
# -----------------

def listar_todos_alunos() -> list[Aluno]:
    """Retorna uma lista de TODOS os alunos cadastrados (ativos e inativos)."""
    session = Session()
    try:
        # Retorna todos os alunos ordenados pelo nome
        alunos = session.query(Aluno).order_by(Aluno.nome_completo).all()
        return alunos
    finally:
        session.close()

def buscar_aluno_por_cpf(cpf: str) -> Aluno | None:
    """Busca um aluno pelo CPF (limpo)."""
    session = Session()
    cpf_limpo = limpar_cpf(cpf)
    try:
        aluno = session.query(Aluno).filter(Aluno.cpf_limpo == cpf_limpo).first()
        return aluno
    finally:
        session.close()

def buscar_aluno_por_id(aluno_id: int) -> Aluno | None:
    """
    Busca um aluno específico pelo ID, carregando (EAGERLY) a Academia 
    e as Matrículas para evitar o Detached Instance Error.
    (Essa correção já havia sido feita anteriormente.)
    """
    session = Session()
    try:
        # Usa .options(joinedload(...)) para carregar os relacionamentos na mesma query.
        aluno = session.query(Aluno).options(
            joinedload(Aluno.academia),      # Carrega a Academia junto
            # Carrega Matriculas e, dentro delas, a Modalidade
            joinedload(Aluno.matriculas).joinedload(Matricula.modalidade) 
        ).filter(Aluno.id == aluno_id).first()
        
        return aluno
    except Exception as e:
        print(f"Erro ao buscar aluno por ID com Eager Loading: {e}") 
        return None
    finally:
        session.close()


def listar_alunos_por_academia(academia_id: int) -> list[Aluno]:
    """Retorna uma lista de alunos ATIVOS de uma academia específica."""
    session = Session()
    try:
        alunos = session.query(Aluno).filter(
            Aluno.academia_id == academia_id, 
            Aluno.status_ativo == True
        ).order_by(Aluno.nome_completo).all()
        return alunos
    finally:
        session.close()


# -----------------
# U: UPDATE (ATUALIZAR)
# -----------------

def atualizar_status_aluno(cpf: str, novo_status: bool) -> bool:
    """Atualiza o status (ativo/inativo) do aluno."""
    session = Session()
    cpf_limpo = limpar_cpf(cpf)
    try:
        aluno = session.query(Aluno).filter(Aluno.cpf_limpo == cpf_limpo).first()
        
        if aluno:
            aluno.status_ativo = novo_status
            session.commit()
            status_str = "ATIVO" if novo_status else "INATIVO"
            print(f"SUCESSO: Status do aluno {aluno.nome_completo} atualizado para {status_str}.")
            return True
        else:
            print(f"ALERTA: Aluno com CPF {cpf} não encontrado.")
            return False
            
    except Exception as e:
        session.rollback()
        print(f"ERRO ao atualizar status do aluno: {e}")
        return False
    finally:
        session.close()

# -----------------
# D: DELETE (DELETAR)
# -----------------

def deletar_aluno(cpf: str) -> bool:
    """Deleta um aluno do banco de dados (ADMIN)."""
    session = Session()
    cpf_limpo = limpar_cpf(cpf)
    try:
        aluno = session.query(Aluno).filter(Aluno.cpf_limpo == cpf_limpo).first()
        
        if aluno:
            nome_aluno = aluno.nome_completo
            
            # Deleta as matrículas associadas primeiro
            session.query(Matricula).filter(Matricula.aluno_id == aluno.id).delete()
            
            session.delete(aluno)
            session.commit()
            print(f"SUCESSO: Aluno {nome_aluno} e suas matrículas foram removidos.")
            return True
        else:
            print(f"ALERTA: Aluno com CPF {cpf} não encontrado para remoção.")
            return False
            
    except Exception as e:
        session.rollback()
        print(f"ERRO ao deletar aluno: {e}")
        return False
    finally:
        session.close()