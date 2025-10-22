import re
import sys
import logging
from datetime import date
from typing import Optional, Callable
from functools import wraps

# Importação dos módulos de serviço
from models import create_database_tables, Academia, Session, Usuario
from aluno_service import (
    cadastrar_aluno,
    buscar_aluno_por_cpf,
    listar_alunos_por_academia,
    listar_todos_alunos,
    atualizar_status_aluno,
    deletar_aluno,
    buscar_aluno_por_id,
)
from academia_service import (
    cadastrar_academia,
    listar_todas_academias,
    atualizar_academia,
    deletar_academia,
)
from modalidade_treinador_service import (
    cadastrar_modalidade,
    listar_modalidades,
    cadastrar_treinador,
    listar_treinadores_por_modalidade,
    deletar_treinador,
)
from matricula_service import (
    matricular_aluno,
    listar_matriculas_aluno,
    atualizar_graduacao,
)
from relatorio_service import (
    contar_alunos_por_academia,
    contar_alunos_por_modalidade_e_graduacao,
)
from auth_service import (
    autenticar_usuario,               # PRECISA RETORNAR USUÁRIO!
    inicializar_usuario_admin,
    registrar_usuario,
    checar_permissao,
    listar_usuarios,
    atualizar_papel_usuario,
    deletar_usuario,
)

logging.basicConfig(
    filename='sec_lutas.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Variáveis globais
session_user = None
ACADEMIA_TESTE_ID = None

def limpar_cpf(cpf: str) -> Optional[str]:
    numeros = re.sub(r'[^0-9]', '', cpf)
    return numeros if len(numeros) == 11 else None

def checar_permissao_decorator(papel_necessario: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            global session_user
            if session_user and checar_permissao(session_user, papel_necessario):
                return func(*args, **kwargs)
            print(f"Acesso negado: '{papel_necessario}' necessário.")
            logging.warning(f"Acesso negado: {session_user.nome if session_user else 'Desconhecido'} tentava acessar '{func.__name__}'")
            return None
        return wrapper
    return decorator

def inicializar_sistema() -> None:
    global ACADEMIA_TESTE_ID
    create_database_tables()
    academias = listar_todas_academias()
    if academias:
        ACADEMIA_TESTE_ID = academias[0].id
    else:
        id_nova = cadastrar_academia("Academia de Teste - Prefeitura")
        ACADEMIA_TESTE_ID = id_nova
    inicializar_usuario_admin()

def tela_de_login() -> None:
    global session_user
    tentativas = 3
    while tentativas > 0:
        if not listar_usuarios():
            print("Nenhum usuário encontrado. Crie o usuário administrador:")
            registrar_usuario("admin", "admin12345", "ADMIN")
            print("Usuário admin criado com senha padrão 'admin12345'")
        usuario = input("Usuário: ").strip()
        senha = input("Senha: ").strip()
        session_user = autenticar_usuario(usuario, senha)  # DEVE RETORNAR OBJETO USUÁRIO!
        if session_user:
            print(f"Bem vindo, {session_user.nome}!")
            logging.info(f"Usuário {session_user.nome} logou com sucesso.")
            return
        else:
            tentativas -= 1
            print(f"Credenciais inválidas. Tentativas restantes: {tentativas}")
            logging.warning("Credenciais inválidas na tentativa de login.")
    print("Número máximo de tentativas excedido. Saindo...")
    sys.exit(0)

def input_validado(prompt: str, pattern: Optional[str] = None, erro_msg: str = "Entrada inválida.") -> str:
    while True:
        entrada = input(prompt).strip()
        if not entrada:
            print("Entrada não pode ser vazia.")
            continue
        if pattern and not re.match(pattern, entrada):
            print(erro_msg)
            continue
        return entrada

def menu_principal() -> None:
    opções = {
        "1": menu_alunos,
        "2": menu_academias,
        "3": menu_modalidades_treinadores,
        "4": menu_matriculas,
        "5": menu_relatorios,
        "6": menu_usuarios,
        "0": sair_sistema
    }
    while True:
        print("\n--- Menu Principal ---")
        print("1 - Alunos")
        print("2 - Academias")
        print("3 - Modalidades e Treinadores")
        print("4 - Matrículas")
        print("5 - Relatórios")
        print("6 - Usuários")
        print("0 - Sair")
        escolha = input_validado("Escolha: ", r"^[0-6]{1}$", "Escolha uma opção válida.")
        if escolha in opções:
            opções[escolha]()
        else:
            print("Opção inválida.")

def sair_sistema() -> None:
    print("Encerrando o sistema. Até logo!")
    logging.info(f"Usuário {session_user.nome if session_user else 'Desconhecido'} encerrou a sessão.")
    sys.exit(0)

@checar_permissao_decorator("VIEWER")
def menu_alunos() -> None:
    opções = {
        "1": opcao_cadastrar_aluno,
        "2": opcao_listar_todos_alunos,
        "3": opcao_buscar_aluno_cpf,
        "4": opcao_listar_alunos_por_academia,
        "5": opcao_atualizar_status_aluno,
        "6": opcao_deletar_aluno,
        "0": lambda: None
    }
    while True:
        print("\n--- Menu Alunos ---")
        print("1 - Cadastrar aluno")
        print("2 - Listar todos os alunos")
        print("3 - Buscar aluno por CPF")
        print("4 - Listar alunos por academia")
        print("5 - Atualizar status do aluno")
        print("6 - Deletar aluno")
        print("0 - Voltar")
        escolha = input_validado("Escolha: ", r"^[0-6]{1}$", "Escolha uma opção válida.")
        if escolha == "0":
            break
        elif escolha in opções:
            opções[escolha]()
        else:
            print("Opção inválida.")

def opcao_cadastrar_aluno() -> None:
    print("\nCadastro de Aluno")
    nome = input_validado("Nome: ")
    cpf = input_validado("CPF (somente números ou com formatação): ")
    cpf_limpo = limpar_cpf(cpf)
    if not cpf_limpo:
        print("CPF inválido.")
        return
    success = cadastrar_aluno(nome, cpf_limpo, ACADEMIA_TESTE_ID)
    if success:
        print("Aluno cadastrado com sucesso.")
        logging.info(f"Aluno {nome} cadastrado por {session_user.nome}.")
    else:
        print("Falha ao cadastrar o aluno.")

def opcao_listar_todos_alunos() -> None:
    print("\nLista de Todos os Alunos")
    alunos = listar_todos_alunos()
    if alunos:
        for aluno in alunos:
            print(f"ID: {aluno.id} | Nome: {aluno.nome} | CPF: {aluno.cpf} | Status: {aluno.status}")
    else:
        print("Nenhum aluno cadastrado.")

def opcao_buscar_aluno_cpf() -> None:
    cpf = input_validado("Informe o CPF para busca: ")
    cpf_limpo = limpar_cpf(cpf)
    if not cpf_limpo:
        print("CPF inválido.")
        return
    aluno = buscar_aluno_por_cpf(cpf_limpo)
    if aluno:
        print(f"Aluno encontrado: ID: {aluno.id} | Nome: {aluno.nome} | Status: {aluno.status}")
    else:
        print("Aluno não encontrado.")

def opcao_listar_alunos_por_academia() -> None:
    print("\nListar alunos por academia")
    academias = listar_todas_academias()
    for academia in academias:
        print(f"ID: {academia.id} | Nome: {academia.nome}")
    academia_id = input_validado("Informe o ID da academia: ", r"^\d+$", "ID inválido.")
    alunos = listar_alunos_por_academia(int(academia_id))
    if alunos:
        for aluno in alunos:
            print(f"ID: {aluno.id} | Nome: {aluno.nome} | Status: {aluno.status}")
    else:
        print("Nenhum aluno encontrado para essa academia.")

def opcao_atualizar_status_aluno() -> None:
    aluno_id = input_validado("Informe o ID do aluno para atualizar status: ", r"^\d+$", "ID inválido.")
    status = input_validado("Informe o novo status: ")
    success = atualizar_status_aluno(int(aluno_id), status)
    if success:
        print("Status atualizado com sucesso.")
        logging.info(f"Status do aluno {aluno_id} atualizado para {status} por {session_user.nome}.")
    else:
        print("Falha ao atualizar o status.")

def opcao_deletar_aluno() -> None:
    aluno_id = input_validado("Informe o ID do aluno para deletar: ", r"^\d+$", "ID inválido.")
    confirmacao = input("Confirma a exclusão? (s/n): ").strip().lower()
    if confirmacao == 's':
        success = deletar_aluno(int(aluno_id))
        if success:
            print("Aluno deletado com sucesso.")
            logging.info(f"Aluno {aluno_id} deletado por {session_user.nome}.")
        else:
            print("Falha ao deletar o aluno.")
    else:
        print("Exclusão cancelada.")

# --- Menus restantes seguem igual ao seu original (academias, modalidades, matriculas, relatórios, usuários)
# --- O que mudaria seria sempre garantir que "session_user" seja o objeto usuário, nunca bool!

# ... [MANTENHA O RESTANTE DO SEU CÓDIGO DOS MENUS COMO JÁ ESTÁ]

def main() -> None:
    inicializar_sistema()
    tela_de_login()
    while True:
        menu_principal()

if __name__ == "__main__":
    main()
