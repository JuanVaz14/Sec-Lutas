from models import Aluno, Academia, Session
from datetime import date
from sqlalchemy.exc import IntegrityError, NoResultFound
from typing import List
import re

# --- Funções Auxiliares de Limpeza (Idealmente estariam em 'utils.py') ---

def limpar_cpf(cpf: str) -> str:
    """Remove pontuação e retorna o CPF como string de 11 dígitos."""
    # O uso de re.sub(r'[^0-9]', '', cpf) remove qualquer caractere que não seja número.
    return re.sub(r'[^0-9]', '', cpf).zfill(11) 

# --- C: CREATE (Cadastrar Novo Aluno) ---

def cadastrar_aluno(nome: str, data_nasc: str, cpf: str, academia_id: int) -> Aluno | None:
    """Cadastra um novo aluno no banco de dados."""
    
    # Limpa o CPF de qualquer formatação para garantir a integridade no DB
    cpf_limpo = limpar_cpf(cpf) 
    
    session = Session()
    try:
        # Verifica se o CPF limpo já existe
        if session.query(Aluno).filter_by(cpf=cpf_limpo).first():
            print(f"ERRO: Aluno com CPF {cpf_limpo} já está cadastrado.")
            return None
        
        # Converte a string da data (formato 'YYYY-MM-DD') para objeto date
        data_nascimento = date.fromisoformat(data_nasc)

        novo_aluno = Aluno(
            nome_completo=nome,
            data_nascimento=data_nascimento,
            cpf=cpf_limpo, # Armazena o CPF limpo no banco
            academia_id=academia_id,
            status_ativo=True # Começa como ativo
        )
        
        session.add(novo_aluno)
        session.commit()
        # Usa a propriedade 'cpf_formatado' da classe Aluno para exibir
        print(f"SUCESSO: Aluno '{nome}' cadastrado. CPF: {novo_aluno.cpf_formatado}")
        return novo_aluno
    
    except ValueError:
        print("ERRO: Formato de data inválido. Use 'YYYY-MM-DD'.")
        session.rollback()
        return None
    except IntegrityError:
        print("ERRO: ID da Academia inválido. Verifique se a Academia existe.")
        session.rollback()
        return None
    finally:
        session.close()

# --- R: READ (Buscar e Listar Alunos) ---

def buscar_aluno_por_cpf(cpf: str) -> Aluno | None:
    """Busca um aluno específico pelo CPF, limpando a entrada antes de buscar."""
    
    # Limpa a entrada para buscar pelo valor armazenado no DB
    cpf_limpo = limpar_cpf(cpf)
    
    session = Session()
    try:
        aluno = session.query(Aluno).filter_by(cpf=cpf_limpo).one_or_none()
        if aluno:
            # Ao retornar o objeto, você pode acessar aluno.cpf_formatado
            return aluno
        return None
    finally:
        session.close()

def listar_alunos_por_academia(academia_id: int) -> List[Aluno]:
    """Lista todos os alunos ativos em uma determinada academia."""
    session = Session()
    try:
        alunos = session.query(Aluno).filter(
            Aluno.academia_id == academia_id,
            Aluno.status_ativo == True
        ).all()
        return alunos
    finally:
        session.close()

# --- U: UPDATE (Atualizar Informações ou Status) ---

def atualizar_status_aluno(cpf: str, status_ativo: bool) -> bool:
    """Atualiza o status (Ativo/Inativo) de um aluno pelo CPF."""
    
    cpf_limpo = limpar_cpf(cpf)
    session = Session()
    
    try:
        aluno = session.query(Aluno).filter_by(cpf=cpf_limpo).one()
        aluno.status_ativo = status_ativo
        session.commit()
        
        status = "ATIVO" if status_ativo else "INATIVO"
        print(f"SUCESSO: Status do aluno '{aluno.nome_completo}' (CPF: {aluno.cpf_formatado}) atualizado para {status}.")
        return True
    except NoResultFound:
        print(f"ERRO: Aluno com CPF {cpf_limpo} não encontrado.")
        session.rollback()
        return False
    finally:
        session.close()
        
# --- D: DELETE (Remover Aluno) ---

def deletar_aluno(cpf: str) -> bool:
    """Remove um aluno permanentemente pelo CPF."""
    
    cpf_limpo = limpar_cpf(cpf)
    session = Session()
    
    try:
        aluno = session.query(Aluno).filter_by(cpf=cpf_limpo).one()
        nome = aluno.nome_completo
        
        session.delete(aluno)
        session.commit()
        print(f"SUCESSO: Aluno '{nome}' (CPF: {aluno.cpf_formatado}) removido permanentemente do cadastro.")
        return True
    except NoResultFound:
        print(f"ERRO: Aluno com CPF {cpf_limpo} não encontrado para deleção.")
        session.rollback()
        return False
    finally:
        session.close()