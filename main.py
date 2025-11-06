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

def limpar_cpf(cpf_raw: str) -> Optional[str]:
    nums = re.sub(r'\D', '', cpf_raw or "")
    return nums if len(nums) == 11 else None

def formatar_telefone(telefone_raw: str) -> str:
    nums = re.sub(r'\D', '', telefone_raw or "")
    if len(nums) == 11:
        return f"({nums[0:2]}) {nums[2:7]}-{nums[7:11]}"
    if len(nums) == 10:
        return f"({nums[0:2]}) {nums[2:6]}-{nums[6:10]}"
    return telefone_raw.strip()

def checar_permissao_decorator(papel_necessario: str):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            global session_user
            if session_user is None:
                print("Acesso negado: usuário não autenticado.")
                logging.warning(f"Acesso negado: usuário desconhecido tentava acessar '{func.__name__}'")
                return
            papel_atual = (getattr(session_user, "papel", "") or "").upper().strip()
            if not checar_permissao(session_user, papel_necessario):
                print(f"Acesso negado: '{papel_necessario}' necessário.")
                logging.warning(f"Acesso negado: {getattr(session_user,'nome_usuario','Desconhecido')} tentou acessar '{func.__name__}' com papel={papel_atual}")
                return
            return func(*args, **kwargs)
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

def tela_de_login():
    print("\n=== Login ===")
    while True:
        nome = input("Usuário: ")
        senha = input("Senha: ")
        
        global session_user
        session_user = autenticar_usuario(nome, senha)
        
        if session_user:
            print(f"Login bem-sucedido para o usuário: {session_user.nome_usuario} ({session_user.papel})")
            # Aqui mudamos de .nome para .nome_usuario
            print(f"Bem vindo, {session_user.nome_usuario}!")
            return
        else:
            print("Credenciais inválidas. Tente novamente.")

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
        print("1 - Menu_Alunos")
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
    logging.info(f"Usuário {session_user.nome_usuario if session_user else 'Desconhecido'} encerrou a sessão.")
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
        logging.info(f"Aluno {nome} cadastrado por {session_user.nome_usuario}.")
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
        logging.info(f"Status do aluno {aluno_id} atualizado para {status} por {session_user.nome_usuario}.")
    else:
        print("Falha ao atualizar o status.")

def opcao_deletar_aluno() -> None:
    aluno_id = input_validado("Informe o ID do aluno para deletar: ", r"^\d+$", "ID inválido.")
    confirmacao = input("Confirma a exclusão? (s/n): ").strip().lower()
    if confirmacao == 's':
        success = deletar_aluno(int(aluno_id))
        if success:
            print("Aluno deletado com sucesso.")
            logging.info(f"Aluno {aluno_id} deletado por {session_user.nome_usuario}.")
        else:
            print("Falha ao deletar o aluno.")
    else:
        print("Exclusão cancelada.")

@checar_permissao_decorator("VIEWER")
def menu_academias() -> None:
    opções = {
        "1": opcao_cadastrar_academia,
        "2": opcao_listar_academias,
        "3": opcao_atualizar_academia,
        "4": opcao_deletar_academia,
        "0": lambda: None
    }
    while True:
        print("\n--- Menu Academias ---")
        print("1 - Cadastrar academia")
        print("2 - Listar academias")
        print("3 - Atualizar academia")
        print("4 - Deletar academia")
        print("0 - Voltar")
        escolha = input_validado("Escolha: ", r"^[0-4]{1}$", "Escolha uma opção válida.")
        if escolha == "0":
            break
        elif escolha in opções:
            opções[escolha]()
        else:
            print("Opção inválida.")

def opcao_cadastrar_academia() -> None:
    print("\nCadastro de Academia")
    nome = input_validado("Nome: ")
    endereco = input_validado("Endereço: ")
    telefone = input_validado("Telefone: ")
    
    success = cadastrar_academia(nome, endereco, telefone)
    if success:
        print("Academia cadastrada com sucesso.")
        logging.info(f"Academia {nome} cadastrada por {session_user.nome_usuario}.")
    else:
        print("Falha ao cadastrar academia.")

def opcao_listar_academias() -> None:
    print("\nLista de Academias")
    academias = listar_todas_academias()
    if academias:
        for academia in academias:
            print(f"ID: {academia.id} | Nome: {academia.nome}")
    else:
        print("Nenhuma academia cadastrada.")

def opcao_atualizar_academia() -> None:
    academia_id = input_validado("Informe o ID da academia: ", r"^\d+$", "ID inválido.")
    nome = input_validado("Novo nome: ")
    endereco = input_validado("Novo endereço: ")
    telefone = input_validado("Novo telefone: ")
    
    success = atualizar_academia(int(academia_id), nome, endereco, telefone)
    if success:
        print("Academia atualizada com sucesso.")
        logging.info(f"Academia {academia_id} atualizada por {session_user.nome_usuario}.")
    else:
        print("Falha ao atualizar academia.")

def opcao_deletar_academia() -> None:
    academia_id = input_validado("Informe o ID da academia: ", r"^\d+$", "ID inválido.")
    confirmacao = input("Confirma a exclusão? (s/n): ").strip().lower()
    if confirmacao == 's':
        success = deletar_academia(int(academia_id))
        if success:
            print("Academia deletada com sucesso.")
            logging.info(f"Academia {academia_id} deletada por {session_user.nome_usuario}.")
        else:
            print("Falha ao deletar academia.")
    else:
        print("Exclusão cancelada.")

@checar_permissao_decorator("VIEWER")
def menu_modalidades_treinadores() -> None:
    opções = {
        "1": opcao_cadastrar_modalidade,
        "2": opcao_listar_modalidades,
        "3": opcao_cadastrar_treinador,
        "4": opcao_listar_treinadores,
        "5": opcao_deletar_treinador,
        "0": lambda: None
    }
    while True:
        print("\n--- Menu Modalidades e Treinadores ---")
        print("1 - Cadastrar modalidade")
        print("2 - Listar modalidades")
        print("3 - Cadastrar treinador")
        print("4 - Listar treinadores")
        print("5 - Deletar treinador")
        print("0 - Voltar")
        escolha = input_validado("Escolha: ", r"^[0-5]{1}$", "Escolha uma opção válida.")
        if escolha == "0":
            break
        elif escolha in opções:
            opções[escolha]()
        else:
            print("Opção inválida.")

def opcao_cadastrar_modalidade() -> None:
    print("\nCadastro de Modalidade")
    nome = input_validado("Nome da modalidade: ")
    success = cadastrar_modalidade(nome)
    if success:
        print("Modalidade cadastrada com sucesso.")
        logging.info(f"Modalidade {nome} cadastrada por {session_user.nome_usuario}")
    else:
        print("Falha ao cadastrar modalidade.")

def opcao_listar_modalidades() -> None:
    print("\nLista de Modalidades")
    modalidades = listar_modalidades()
    if modalidades:
        for modalidade in modalidades:
            print(f"ID: {modalidade.id} | Nome: {modalidade.nome}")
    else:
        print("Nenhuma modalidade cadastrada.")

def opcao_cadastrar_treinador() -> None:
    print("\nCadastro de Treinador")
    nome = input_validado("Nome do treinador: ")
    modalidades = listar_modalidades()
    if not modalidades:
        print("Não há modalidades cadastradas. Cadastre uma modalidade primeiro.")
        return
    
    print("\nModalidades disponíveis:")
    for modalidade in modalidades:
        print(f"ID: {modalidade.id} | Nome: {modalidade.nome}")
    
    modalidade_id = input_validado("ID da modalidade: ", r"^\d+$", "ID inválido.")
    success = cadastrar_treinador(nome, int(modalidade_id))
    if success:
        print("Treinador cadastrado com sucesso.")
        logging.info(f"Treinador {nome} cadastrado por {session_user.nome_usuario}")
    else:
        print("Falha ao cadastrar treinador.")

def opcao_listar_treinadores() -> None:
    print("\nLista de Treinadores por Modalidade")
    modalidades = listar_modalidades()
    if not modalidades:
        print("Não há modalidades cadastradas.")
        return
    
    for modalidade in modalidades:
        print(f"\nModalidade: {modalidade.nome}")
        treinadores = listar_treinadores_por_modalidade(modalidade.id)
        if treinadores:
            for treinador in treinadores:
                print(f"ID: {treinador.id} | Nome: {treinador.nome}")
        else:
            print("Nenhum treinador cadastrado para esta modalidade.")

def opcao_deletar_treinador() -> None:
    treinador_id = input_validado("ID do treinador para deletar: ", r"^\d+$", "ID inválido.")
    confirmacao = input("Confirma a exclusão? (s/n): ").strip().lower()
    if confirmacao == 's':
        success = deletar_treinador(int(treinador_id))
        if success:
            print("Treinador deletado com sucesso.")
            logging.info(f"Treinador {treinador_id} deletado por {session_user.nome_usuario}")
        else:
            print("Falha ao deletar treinador.")
    else:
        print("Exclusão cancelada.")

@checar_permissao_decorator("VIEWER")
def menu_matriculas() -> None:
    opções = {
        "1": opcao_matricular_aluno,
        "2": opcao_listar_matriculas_aluno,
        "3": opcao_atualizar_graduacao,
        "0": lambda: None
    }
    while True:
        print("\n--- Menu Matrículas ---")
        print("1 - Matricular aluno")
        print("2 - Listar matrículas do aluno")
        print("3 - Atualizar graduação")
        print("0 - Voltar")
        escolha = input_validado("Escolha: ", r"^[0-3]{1}$", "Escolha uma opção válida.")
        if escolha == "0":
            break
        elif escolha in opções:
            opções[escolha]()
        else:
            print("Opção inválida.")

def opcao_matricular_aluno() -> None:
    print("\nMatricular Aluno (CPF será usado para identificar; matrícula = ID do aluno)")

    nome = input_validado("Nome completo: ").strip()
    if not nome:
        print("Nome inválido.")
        return
    nome_upper = nome.upper()

    telefone_raw = input_validado("Telefone: ").strip()
    telefone_formatado = formatar_telefone(telefone_raw)

    cpf_raw = input_validado("CPF: ").strip()
    cpf_limpo = limpar_cpf(cpf_raw)
    if not cpf_limpo:
        print("CPF inválido. Informe 11 dígitos.")
        return
    cpf_formatado = f"{cpf_limpo[0:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:11]}"

    # Selecionar polo (academia)
    academias = listar_todas_academias()
    if not academias:
        print("Nenhuma academia cadastrada. Cadastre uma academia antes.")
        return
    print("\nAcademias disponíveis:")
    for a in academias:
        print(f"ID: {a.id} | Nome: {a.nome}")
    academia_id = input_validado("ID da academia (polo): ", r"^\d+$", "ID inválido.")
    academia_id = int(academia_id)

    # Graduação inicial e responsável
    graduacao = input_validado("Graduação inicial: ").strip().upper()
    responsavel = input_validado("Nome do responsável: ").strip().upper()

    # Verifica se aluno já existe
    aluno = buscar_aluno_por_cpf(cpf_limpo)
    if aluno:
        aluno_id = aluno.id
        print(f"Aluno já cadastrado: ID {aluno_id} | Nome: {aluno.nome_completo}")
        # atualizar telefone/responsavel/graduacao se desejar
    else:
        novo_id = cadastrar_aluno(
            nome_completo=nome_upper,
            cpf_limpo=cpf_limpo,
            academia_id=academia_id,
            graduacao=graduacao,
            responsavel=responsavel,
            telefone=telefone_formatado
        )
        if not novo_id:
            print("Falha ao cadastrar aluno (CPF possivelmente já cadastrado).")
            return
        aluno_id = novo_id
        print(f"Aluno cadastrado com sucesso. ID = {aluno_id}")

    # Selecionar modalidade para matrícula
    modalidades = listar_modalidades()
    if not modalidades:
        print("Não há modalidades cadastradas. Cadastre uma modalidade primeiro.")
        return
    print("\nModalidades disponíveis:")
    for m in modalidades:
        print(f"ID: {m.id} | Nome: {m.nome}")
    modalidade_id = input_validado("ID da modalidade: ", r"^\d+$", "ID inválido.")
    modalidade_id = int(modalidade_id)

    # Cria matrícula usando ID do aluno como número_matricula
    success = matricular_aluno(aluno_id, modalidade_id, graduacao)
    if success:
        print(f"Matrícula realizada com sucesso. Número da matrícula: {aluno_id}")
    else:
        print("Falha ao realizar matrícula.")

def opcao_listar_matriculas_aluno() -> None:
    print("\nListar Matrículas do Aluno")
    aluno_id = input_validado("ID do aluno: ", r"^\d+$", "ID inválido.")
    
    aluno = buscar_aluno_por_id(int(aluno_id))
    if not aluno:
        print("Aluno não encontrado.")
        return
    
    print(f"\nMatrículas do aluno: {aluno.nome}")
    matriculas = listar_matriculas_aluno(int(aluno_id))
    if matriculas:
        for matricula in matriculas:
            print(f"Modalidade: {matricula.modalidade.nome} | Graduação: {matricula.graduacao}")
    else:
        print("Nenhuma matrícula encontrada.")

def opcao_atualizar_graduacao() -> None:
    print("\nAtualizar Graduação")
    aluno_id = input_validado("ID do aluno: ", r"^\d+$", "ID inválido.")
    modalidade_id = input_validado("ID da modalidade: ", r"^\d+$", "ID inválido.")
    nova_graduacao = input_validado("Nova graduação: ")
    
    success = atualizar_graduacao(int(aluno_id), int(modalidade_id), nova_graduacao)
    if success:
        print("Graduação atualizada com sucesso.")
        logging.info(f"Graduação do aluno {aluno_id} atualizada por {session_user.nome_usuario}")
    else:
        print("Falha ao atualizar graduação.")

@checar_permissao_decorator("VIEWER")
def menu_relatorios() -> None:
    opções = {
        "1": opcao_relatorio_alunos_academia,
        "2": opcao_relatorio_alunos_modalidade,
        "0": lambda: None
    }
    while True:
        print("\n--- Menu Relatórios ---")
        print("1 - Alunos por Academia")
        print("2 - Alunos por Modalidade")
        print("0 - Voltar")
        escolha = input_validado("Escolha: ", r"^[0-2]{1}$", "Escolha uma opção válida.")
        if escolha == "0":
            break
        elif escolha in opções:
            opções[escolha]()
        else:
            print("Opção inválida.")

def opcao_relatorio_alunos_academia() -> None:
    print("\nRelatório - Alunos por Academia")
    contagem = contar_alunos_por_academia()
    for academia_id, total in contagem.items():
        print(f"Academia ID {academia_id}: {total} alunos")

def opcao_relatorio_alunos_modalidade() -> None:
    print("\nRelatório - Alunos por Modalidade e Graduação")
    contagem = contar_alunos_por_modalidade_e_graduacao()
    for modalidade_id, graduacoes in contagem.items():
        print(f"\nModalidade ID {modalidade_id}:")
        for graduacao, total in graduacoes.items():
            print(f"  {graduacao}: {total} alunos")

@checar_permissao_decorator("ADMIN")
def menu_usuarios() -> None:
    opções = {
        "1": opcao_registrar_usuario,
        "2": opcao_listar_usuarios,
        "3": opcao_atualizar_papel_usuario,
        "4": opcao_deletar_usuario,
        "0": lambda: None
    }
    while True:
        print("\n--- Menu Usuários ---")
        print("1 - Registrar usuário")
        print("2 - Listar usuários")
        print("3 - Atualizar papel")
        print("4 - Deletar usuário")
        print("0 - Voltar")
        escolha = input_validado("Escolha: ", r"^[0-4]{1}$", "Escolha uma opção válida.")
        if escolha == "0":
            break
        elif escolha in opções:
            opções[escolha]()
        else:
            print("Opção inválida.")

def opcao_registrar_usuario() -> None:
    print("\nRegistro de Usuário")
    nome = input_validado("Nome de usuário: ")
    senha = input_validado("Senha: ")
    papel = input_validado("Papel (ADMIN/VIEWER): ", r"^(ADMIN|VIEWER)$", "Papel inválido.")
    
    success = registrar_usuario(nome, senha, papel)
    if success:
        print("Usuário registrado com sucesso.")
        logging.info(f"Usuário {nome} registrado por {session_user.nome_usuario}")
    else:
        print("Falha ao registrar usuário.")

def opcao_listar_usuarios() -> None:
    print("\nLista de Usuários")
    usuarios = listar_usuarios()
    if usuarios:
        for usuario in usuarios:
            print(f"ID: {usuario.id} | Nome: {usuario.nome_usuario} | Papel: {usuario.papel}")
    else:
        print("Nenhum usuário cadastrado.")

def opcao_atualizar_papel_usuario() -> None:
    nome = input_validado("Nome do usuário: ")
    novo_papel = input_validado("Novo papel (ADMIN/VIEWER): ", r"^(ADMIN|VIEWER)$", "Papel inválido.")
    
    success = atualizar_papel_usuario(nome, novo_papel)
    if success:
        print("Papel atualizado com sucesso.")
        logging.info(f"Papel do usuário {nome} atualizado para {novo_papel} por {session_user.nome_usuario}")
    else:
        print("Falha ao atualizar papel.")

def opcao_deletar_usuario() -> None:
    nome = input_validado("Nome do usuário para deletar: ")
    if nome == session_user.nome_usuario:
        print("Não é possível deletar o próprio usuário.")
        return
    
    confirmacao = input("Confirma a exclusão? (s/n): ").strip().lower()
    if confirmacao == 's':
        success = deletar_usuario(nome)
        if success:
            print("Usuário deletado com sucesso.")
            logging.info(f"Usuário {nome} deletado por {session_user.nome_usuario}")
        else:
            print("Falha ao deletar usuário.")
    else:
        print("Exclusão cancelada.")

# --- Menus restantes seguem igual ao seu original (modalidades, matriculas, relatórios, usuários)
# --- O que mudaria seria sempre garantir que "session_user" seja o objeto usuário, nunca bool!

# ... [MANTENHA O RESTANTE DO SEU CÓDIGO DOS MENUS COMO JÁ ESTÁ]

def main() -> None:
    inicializar_sistema()
    tela_de_login()
    while True:
        menu_principal()

if __name__ == "__main__":
    main()
