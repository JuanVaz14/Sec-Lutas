# main.py - VERSÃO CORRIGIDA

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
    listar_todos_alunos,
    listar_alunos_por_academia,
    atualizar_status_aluno,
    deletar_aluno,
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
    autenticar_usuario,
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
    """Remove caracteres não numéricos e valida CPF."""
    nums = re.sub(r'\D', '', cpf_raw or "")
    return nums if len(nums) == 11 else None

def formatar_telefone(telefone_raw: str) -> str:
    """Formata telefone para padrão brasileiro."""
    nums = re.sub(r'\D', '', telefone_raw or "")
    if len(nums) == 11:
        return f"({nums[0:2]}) {nums[2:7]}-{nums[7:11]}"
    if len(nums) == 10:
        return f"({nums[0:2]}) {nums[2:6]}-{nums[6:10]}"
    return telefone_raw.strip()

def checar_permissao_decorator(papel_necessario: str):
    """Decorator para proteger funções com verificação de permissão."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            global session_user
            if session_user is None:
                print("\n❌ ACESSO NEGADO: Você precisa estar logado.")
                logging.warning(f"Acesso negado: usuário desconhecido tentava acessar '{func.__name__}'")
                input("\nPressione ENTER para continuar...")
                return
            
            if not checar_permissao(session_user, papel_necessario):
                print(f"\n❌ ACESSO NEGADO: Você precisa ter permissão de '{papel_necessario}'.")
                print(f"   Seu nível atual: {session_user.papel}")
                logging.warning(f"Acesso negado: {session_user.nome_usuario} tentou acessar '{func.__name__}'")
                input("\nPressione ENTER para continuar...")
                return
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def inicializar_sistema() -> None:
    """Inicializa o banco de dados e cria academia de teste."""
    global ACADEMIA_TESTE_ID
    
    print("\n🔧 Inicializando sistema...")
    create_database_tables()
    
    academias = listar_todas_academias()
    if academias:
        ACADEMIA_TESTE_ID = academias[0].id
        print(f"✅ Academia padrão: {academias[0].nome} (ID: {ACADEMIA_TESTE_ID})")
    else:
        print("⚠️  Nenhuma academia encontrada. Criando academia de teste...")
        id_nova = cadastrar_academia("Academia de Teste - Prefeitura", "Endereço Teste", "Responsável Teste")
        ACADEMIA_TESTE_ID = id_nova
    
    inicializar_usuario_admin()
    print("✅ Sistema inicializado com sucesso!\n")

def tela_de_login():
    """Tela de login do sistema."""
    print("\n" + "="*50)
    print("  SISTEMA DE GESTÃO - SECRETARIA DE LUTAS")
    print("="*50)
    
    while True:
        print("\n=== LOGIN ===")
        nome = input("Usuário: ").strip()
        senha = input("Senha: ").strip()
        
        if not nome or not senha:
            print("❌ Usuário e senha não podem estar vazios!")
            continue
        
        global session_user
        session_user = autenticar_usuario(nome, senha)
        
        if session_user:
            print(f"\n✅ Login bem-sucedido!")
            print(f"   Usuário: {session_user.nome_usuario}")
            print(f"   Nível de acesso: {session_user.papel}")
            input("\nPressione ENTER para continuar...")
            return
        else:
            print("\n❌ Credenciais inválidas. Tente novamente.")
            tentar_novamente = input("Tentar novamente? (s/n): ").strip().lower()
            if tentar_novamente != 's':
                print("Encerrando o sistema...")
                sys.exit(0)

def input_validado(prompt: str, pattern: Optional[str] = None, erro_msg: str = "Entrada inválida.") -> str:
    """Solicita entrada do usuário com validação."""
    while True:
        entrada = input(prompt).strip()
        if not entrada:
            print("❌ Entrada não pode ser vazia.")
            continue
        if pattern and not re.match(pattern, entrada):
            print(f"❌ {erro_msg}")
            continue
        return entrada

def menu_principal() -> None:
    """Menu principal do sistema."""
    opcoes = {
        "1": menu_alunos,
        "2": menu_academias,
        "3": menu_modalidades_treinadores,
        "4": menu_matriculas,
        "5": menu_relatorios,
        "6": menu_usuarios,
        "0": sair_sistema
    }
    
    while True:
        print("\n" + "="*50)
        print("           MENU PRINCIPAL")
        print("="*50)
        print(f"Logado como: {session_user.nome_usuario} ({session_user.papel})")
        print("-"*50)
        print("1 - Gerenciar Alunos")
        print("2 - Gerenciar Academias")
        print("3 - Modalidades e Treinadores")
        print("4 - Matrículas")
        print("5 - Relatórios")
        print("6 - Gerenciar Usuários (ADMIN)")
        print("0 - Sair")
        print("="*50)
        
        escolha = input("Escolha uma opção: ").strip()
        
        if escolha in opcoes:
            opcoes[escolha]()
        else:
            print("❌ Opção inválida! Tente novamente.")
            input("\nPressione ENTER para continuar...")

def sair_sistema() -> None:
    """Encerra o sistema."""
    print("\n" + "="*50)
    print("  Encerrando o sistema. Até logo!")
    print("="*50)
    logging.info(f"Usuário {session_user.nome_usuario if session_user else 'Desconhecido'} encerrou a sessão.")
    sys.exit(0)

# ============================================================
# MENUS DE ALUNOS
# ============================================================

@checar_permissao_decorator("VIEWER")
def menu_alunos() -> None:
    """Menu de gerenciamento de alunos."""
    opcoes = {
        "1": opcao_cadastrar_aluno,
        "2": opcao_listar_todos_alunos,
        "3": opcao_buscar_aluno_cpf,
        "4": opcao_listar_alunos_por_academia,
        "5": opcao_atualizar_status_aluno,
        "6": opcao_deletar_aluno,
        "0": lambda: None
    }
    
    while True:
        print("\n" + "-"*50)
        print("         MENU ALUNOS")
        print("-"*50)
        print("1 - Cadastrar aluno")
        print("2 - Listar todos os alunos")
        print("3 - Buscar aluno por CPF")
        print("4 - Listar alunos por academia")
        print("5 - Atualizar status do aluno")
        print("6 - Deletar aluno")
        print("0 - Voltar")
        print("-"*50)
        
        escolha = input("Escolha: ").strip()
        
        if escolha == "0":
            break
        elif escolha in opcoes:
            opcoes[escolha]()
        else:
            print("❌ Opção inválida.")
            input("\nPressione ENTER para continuar...")

def opcao_cadastrar_aluno() -> None:
    """Cadastra um novo aluno."""
    print("\n--- CADASTRO DE ALUNO ---")
    
    nome = input_validado("Nome completo: ")
    cpf = input_validado("CPF (somente números): ", r"^\d{11}$", "CPF deve ter 11 dígitos.")
    
    # Verifica se CPF já existe
    aluno_existe = buscar_aluno_por_cpf(cpf)
    if aluno_existe:
        print(f"\n❌ ERRO: CPF já cadastrado para: {aluno_existe.nome_completo}")
        input("\nPressione ENTER para continuar...")
        return
    
    telefone = input("Telefone (opcional): ").strip()
    responsavel = input("Responsável (opcional): ").strip()
    graduacao = input("Graduação inicial (opcional): ").strip()
    
    aluno_id = cadastrar_aluno(
        nome_completo=nome,
        cpf_limpo=cpf,
        academia_id=ACADEMIA_TESTE_ID,
        graduacao=graduacao,
        responsavel=responsavel,
        telefone=formatar_telefone(telefone) if telefone else ""
    )
    
    if aluno_id:
        print(f"\n✅ Aluno cadastrado com sucesso! ID: {aluno_id}")
        logging.info(f"Aluno {nome} cadastrado por {session_user.nome_usuario}.")
    else:
        print("\n❌ Falha ao cadastrar o aluno.")
    
    input("\nPressione ENTER para continuar...")

def opcao_listar_todos_alunos() -> None:
    """Lista todos os alunos cadastrados."""
    print("\n--- LISTA DE TODOS OS ALUNOS ---")
    
    alunos = listar_todos_alunos()
    
    if not alunos:
        print("⚠️  Nenhum aluno cadastrado.")
        input("\nPressione ENTER para continuar...")
        return
    
    print(f"\nTotal de alunos: {len(alunos)}\n")
    print(f"{'ID':<5} {'Nome':<30} {'CPF':<15} {'Status':<10}")
    print("-" * 70)
    
    for aluno in alunos:
        status = "ATIVO" if aluno.status_ativo else "INATIVO"
        print(f"{aluno.id:<5} {aluno.nome_completo[:29]:<30} {aluno.cpf_formatado:<15} {status:<10}")
    
    input("\nPressione ENTER para continuar...")

def opcao_buscar_aluno_cpf() -> None:
    """Busca um aluno por CPF."""
    print("\n--- BUSCAR ALUNO POR CPF ---")
    
    cpf = input_validado("Informe o CPF (somente números): ", r"^\d{11}$", "CPF deve ter 11 dígitos.")
    
    aluno = buscar_aluno_por_cpf(cpf)
    
    if aluno:
        print("\n✅ ALUNO ENCONTRADO:")
        print(f"   ID: {aluno.id}")
        print(f"   Nome: {aluno.nome_completo}")
        print(f"   CPF: {aluno.cpf_formatado}")
        print(f"   Telefone: {aluno.telefone or 'Não informado'}")
        print(f"   Responsável: {aluno.responsavel or 'Não informado'}")
        print(f"   Graduação: {aluno.graduacao or 'Não informado'}")
        print(f"   Status: {'ATIVO' if aluno.status_ativo else 'INATIVO'}")
    else:
        print("\n❌ Aluno não encontrado.")
    
    input("\nPressione ENTER para continuar...")

def opcao_listar_alunos_por_academia() -> None:
    """Lista alunos de uma academia específica."""
    print("\n--- LISTAR ALUNOS POR ACADEMIA ---")
    
    academias = listar_todas_academias()
    
    if not academias:
        print("⚠️  Nenhuma academia cadastrada.")
        input("\nPressione ENTER para continuar...")
        return
    
    print("\nAcademias disponíveis:")
    for academia in academias:
        print(f"  {academia.id} - {academia.nome}")
    
    academia_id = input_validado("\nID da academia: ", r"^\d+$", "ID inválido.")
    
    alunos = listar_alunos_por_academia(int(academia_id))
    
    if not alunos:
        print("\n⚠️  Nenhum aluno ativo encontrado para essa academia.")
        input("\nPressione ENTER para continuar...")
        return
    
    print(f"\n✅ Total de alunos ativos: {len(alunos)}\n")
    print(f"{'ID':<5} {'Nome':<30} {'CPF':<15}")
    print("-" * 50)
    
    for aluno in alunos:
        print(f"{aluno.id:<5} {aluno.nome_completo[:29]:<30} {aluno.cpf_formatado:<15}")
    
    input("\nPressione ENTER para continuar...")

def opcao_atualizar_status_aluno() -> None:
    """Atualiza o status de um aluno."""
    print("\n--- ATUALIZAR STATUS DO ALUNO ---")
    
    aluno_id = input_validado("ID do aluno: ", r"^\d+$", "ID inválido.")
    
    aluno = buscar_aluno_por_id(int(aluno_id))
    if not aluno:
        print(f"\n❌ Aluno com ID {aluno_id} não encontrado.")
        input("\nPressione ENTER para continuar...")
        return
    
    status_atual = "ATIVO" if aluno.status_ativo else "INATIVO"
    print(f"\nAluno: {aluno.nome_completo}")
    print(f"Status atual: {status_atual}")
    
    print("\nNovo status:")
    print("1 - ATIVO")
    print("2 - INATIVO")
    
    escolha = input_validado("Escolha: ", r"^[12]$", "Escolha 1 ou 2.")
    novo_status = True if escolha == "1" else False
    
    if atualizar_status_aluno(int(aluno_id), novo_status):
        logging.info(f"Status do aluno {aluno_id} atualizado por {session_user.nome_usuario}.")
    
    input("\nPressione ENTER para continuar...")

def opcao_deletar_aluno() -> None:
    """Deleta um aluno do sistema."""
    print("\n--- DELETAR ALUNO ---")
    
    aluno_id = input_validado("ID do aluno: ", r"^\d+$", "ID inválido.")
    
    aluno = buscar_aluno_por_id(int(aluno_id))
    if not aluno:
        print(f"\n❌ Aluno com ID {aluno_id} não encontrado.")
        input("\nPressione ENTER para continuar...")
        return
    
    print(f"\n⚠️  ATENÇÃO: Você está prestes a deletar:")
    print(f"   Nome: {aluno.nome_completo}")
    print(f"   CPF: {aluno.cpf_formatado}")
    
    confirmacao = input("\nConfirma a exclusão? (sim/não): ").strip().lower()
    
    if confirmacao == 'sim':
        if deletar_aluno(int(aluno_id)):
            logging.info(f"Aluno {aluno_id} deletado por {session_user.nome_usuario}.")
    else:
        print("\n❌ Exclusão cancelada.")
    
    input("\nPressione ENTER para continuar...")

# ============================================================
# MENUS DE ACADEMIAS
# ============================================================

@checar_permissao_decorator("VIEWER")
def menu_academias() -> None:
    """Menu de gerenciamento de academias."""
    opcoes = {
        "1": opcao_cadastrar_academia,
        "2": opcao_listar_academias,
        "3": opcao_atualizar_academia,
        "4": opcao_deletar_academia,
        "0": lambda: None
    }
    
    while True:
        print("\n" + "-"*50)
        print("         MENU ACADEMIAS")
        print("-"*50)
        print("1 - Cadastrar academia")
        print("2 - Listar academias")
        print("3 - Atualizar academia")
        print("4 - Deletar academia")
        print("0 - Voltar")
        print("-"*50)
        
        escolha = input("Escolha: ").strip()
        
        if escolha == "0":
            break
        elif escolha in opcoes:
            opcoes[escolha]()
        else:
            print("❌ Opção inválida.")
            input("\nPressione ENTER para continuar...")

def opcao_cadastrar_academia() -> None:
    """Cadastra uma nova academia."""
    print("\n--- CADASTRO DE ACADEMIA ---")
    
    nome = input_validado("Nome: ")
    endereco = input("Endereço: ").strip()
    responsavel = input("Responsável: ").strip()
    
    academia_id = cadastrar_academia(nome, endereco, responsavel)
    
    if academia_id:
        print(f"\n✅ Academia cadastrada com sucesso! ID: {academia_id}")
        logging.info(f"Academia {nome} cadastrada por {session_user.nome_usuario}.")
    else:
        print("\n❌ Falha ao cadastrar academia.")
    
    input("\nPressione ENTER para continuar...")

def opcao_listar_academias() -> None:
    """Lista todas as academias."""
    print("\n--- LISTA DE ACADEMIAS ---")
    
    academias = listar_todas_academias()
    
    if not academias:
        print("⚠️  Nenhuma academia cadastrada.")
        input("\nPressione ENTER para continuar...")
        return
    
    print(f"\nTotal de academias: {len(academias)}\n")
    print(f"{'ID':<5} {'Nome':<30} {'Responsável':<25}")
    print("-" * 60)
    
    for academia in academias:
        print(f"{academia.id:<5} {academia.nome[:29]:<30} {(academia.responsavel or 'N/A')[:24]:<25}")
    
    input("\nPressione ENTER para continuar...")

def opcao_atualizar_academia() -> None:
    """Atualiza informações de uma academia."""
    print("\n--- ATUALIZAR ACADEMIA ---")
    
    academias = listar_todas_academias()
    if not academias:
        print("⚠️  Nenhuma academia cadastrada.")
        input("\nPressione ENTER para continuar...")
        return
    
    print("\nAcademias disponíveis:")
    for academia in academias:
        print(f"  {academia.id} - {academia.nome}")
    
    academia_id = input_validado("\nID da academia: ", r"^\d+$", "ID inválido.")
    
    print("\nDeixe em branco para manter o valor atual:")
    nome = input("Novo nome: ").strip()
    endereco = input("Novo endereço: ").strip()
    responsavel = input("Novo responsável: ").strip()
    
    if atualizar_academia(
        int(academia_id),
        nome=nome if nome else None,
        endereco=endereco if endereco else None,
        responsavel=responsavel if responsavel else None
    ):
        logging.info(f"Academia {academia_id} atualizada por {session_user.nome_usuario}.")
    
    input("\nPressione ENTER para continuar...")

def opcao_deletar_academia() -> None:
    """Deleta uma academia."""
    print("\n--- DELETAR ACADEMIA ---")
    
    academias = listar_todas_academias()
    if not academias:
        print("⚠️  Nenhuma academia cadastrada.")
        input("\nPressione ENTER para continuar...")
        return
    
    print("\nAcademias disponíveis:")
    for academia in academias:
        print(f"  {academia.id} - {academia.nome}")
    
    academia_id = input_validado("\nID da academia: ", r"^\d+$", "ID inválido.")
    
    confirmacao = input("\n⚠️  Confirma a exclusão? (sim/não): ").strip().lower()
    
    if confirmacao == 'sim':
        if deletar_academia(int(academia_id)):
            logging.info(f"Academia {academia_id} deletada por {session_user.nome_usuario}.")
    else:
        print("\n❌ Exclusão cancelada.")
    
    input("\nPressione ENTER para continuar...")

# ============================================================
# MENUS DE MODALIDADES E TREINADORES
# ============================================================

@checar_permissao_decorator("VIEWER")
def menu_modalidades_treinadores() -> None:
    """Menu de modalidades e treinadores."""
    opcoes = {
        "1": opcao_cadastrar_modalidade,
        "2": opcao_listar_modalidades,
        "3": opcao_cadastrar_treinador,
        "4": opcao_listar_treinadores,
        "5": opcao_deletar_treinador,
        "0": lambda: None
    }
    
    while True:
        print("\n" + "-"*50)
        print("    MENU MODALIDADES E TREINADORES")
        print("-"*50)
        print("1 - Cadastrar modalidade")
        print("2 - Listar modalidades")
        print("3 - Cadastrar treinador")
        print("4 - Listar treinadores")
        print("5 - Deletar treinador")
        print("0 - Voltar")
        print("-"*50)
        
        escolha = input("Escolha: ").strip()
        
        if escolha == "0":
            break
        elif escolha in opcoes:
            opcoes[escolha]()
        else:
            print("❌ Opção inválida.")
            input("\nPressione ENTER para continuar...")

def opcao_cadastrar_modalidade() -> None:
    """Cadastra uma nova modalidade."""
    print("\n--- CADASTRO DE MODALIDADE ---")
    
    nome = input_validado("Nome da modalidade: ")
    tipo = input("Tipo (Base/Alto Rendimento): ").strip() or "Base"
    
    if cadastrar_modalidade(nome, tipo):
        logging.info(f"Modalidade {nome} cadastrada por {session_user.nome_usuario}")
    
    input("\nPressione ENTER para continuar...")

def opcao_listar_modalidades() -> None:
    """Lista todas as modalidades."""
    print("\n--- LISTA DE MODALIDADES ---")
    
    modalidades = listar_modalidades()
    
    if not modalidades:
        print("⚠️  Nenhuma modalidade cadastrada.")
        input("\nPressione ENTER para continuar...")
        return
    
    print(f"\nTotal de modalidades: {len(modalidades)}\n")
    print(f"{'ID':<5} {'Nome':<30} {'Tipo':<20}")
    print("-" * 55)
    
    for modalidade in modalidades:
        print(f"{modalidade.id:<5} {modalidade.nome[:29]:<30} {(modalidade.tipo or 'N/A')[:19]:<20}")
    
    input("\nPressione ENTER para continuar...")

def opcao_cadastrar_treinador() -> None:
    """Cadastra um novo treinador."""
    print("\n--- CADASTRO DE TREINADOR ---")
    
    modalidades = listar_modalidades()
    if not modalidades:
        print("⚠️  Não há modalidades cadastradas. Cadastre uma modalidade primeiro.")
        input("\nPressione ENTER para continuar...")
        return
    
    nome = input_validado("Nome do treinador: ")
    telefone = input("Telefone: ").strip()
    certificacao = input("Certificação: ").strip()
    
    print("\nModalidades disponíveis:")
    for modalidade in modalidades:
        print(f"  {modalidade.id} - {modalidade.nome}")
    
    modalidade_id = input_validado("ID da modalidade: ", r"^\d+$", "ID inválido.")
    
    if cadastrar_treinador(nome, int(modalidade_id), telefone, certificacao, ACADEMIA_TESTE_ID):
        logging.info(f"Treinador {nome} cadastrado por {session_user.nome_usuario}")
    
    input("\nPressione ENTER para continuar...")

def opcao_listar_treinadores() -> None:
    """Lista todos os treinadores por modalidade."""
    print("\n--- LISTA DE TREINADORES POR MODALIDADE ---")
    
    modalidades = listar_modalidades()
    if not modalidades:
        print("⚠️  Não há modalidades cadastradas.")
        input("\nPressione ENTER para continuar...")
        return
    
    for modalidade in modalidades:
        print(f"\n📋 Modalidade: {modalidade.nome}")
        print("-" * 50)
        treinadores = listar_treinadores_por_modalidade(modalidade.id)
        
        if treinadores:
            for treinador in treinadores:
                print(f"  ID: {treinador.id} | Nome: {treinador.nome_completo}")
        else:
            print("  ⚠️  Nenhum treinador cadastrado.")
    
    input("\nPressione ENTER para continuar...")

def opcao_deletar_treinador() -> None:
    """Deleta um treinador."""
    print("\n--- DELETAR TREINADOR ---")
    
    treinador_id = input_validado("ID do treinador: ", r"^\d+$", "ID inválido.")
    
    confirmacao = input("\n⚠️  Confirma a exclusão? (sim/não): ").strip().lower()
    
    if confirmacao == 'sim':
        if deletar_treinador(int(treinador_id)):
            logging.info(f"Treinador {treinador_id} deletado por {session_user.nome_usuario}")
    else:
        print("\n❌ Exclusão cancelada.")
    
    input("\nPressione ENTER para continuar...")

# ============================================================
# MENUS DE MATRÍCULAS
# ============================================================

@checar_permissao_decorator("VIEWER")
def menu_matriculas() -> None:
    """Menu de matrículas."""
    opcoes = {
        "1": opcao_matricular_aluno,
        "2": opcao_listar_matriculas_aluno,
        "3": opcao_atualizar_graduacao,
        "0": lambda: None
    }
    
    while True:
        print("\n" + "-"*50)
        print("         MENU MATRÍCULAS")
        print("-"*50)
        print("1 - Matricular aluno")
        print("2 - Listar matrículas do aluno")
        print("3 - Atualizar graduação")
        print("0 - Voltar")
        print("-"*50)
        
        escolha = input("Escolha: ").strip()
        
        if escolha == "0":
            break
        elif escolha in opcoes:
            opcoes[escolha]()
        else:
            print("❌ Opção inválida.")
            input("\nPressione ENTER para continuar...")

def opcao_matricular_aluno() -> None:
    """Matricula um aluno em uma modalidade."""
    print("\n--- MATRICULAR ALUNO ---")
    
    cpf = input_validado("CPF do aluno: ", r"^\d{11}$", "CPF deve ter 11 dígitos.")
    
    aluno = buscar_aluno_por_cpf(cpf)
    
    if not aluno:
        print("\n❌ Aluno não encontrado.")
        criar = input("Deseja cadastrar um novo aluno? (s/n): ").strip().lower()
        
        if criar == 's':
            opcao_cadastrar_aluno()
            return
        else:
            input("\nPressione ENTER para continuar...")
            return
    
    print(f"\nAluno: {aluno.nome_completo}")
    
    modalidades = listar_modalidades()
    if not modalidades:
        print("⚠️  Não há modalidades cadastradas.")
        input("\nPressione ENTER para continuar...")
        return
    
    print("\nModalidades disponíveis:")
    for m in modalidades:
        print(f"  {m.id} - {m.nome}")
    
    modalidade_id = input_validado("ID da modalidade: ", r"^\d+$", "ID inválido.")
    graduacao = input("Graduação inicial: ").strip()
    
    if matricular_aluno(aluno.id, int(modalidade_id), graduacao):
        print(f"\n✅ Matrícula realizada com sucesso! Número: {aluno.id}")
    else:
        print("\n❌ Falha ao realizar matrícula.")
    
    input("\nPressione ENTER para continuar...")

def opcao_listar_matriculas_aluno() -> None:
    """Lista todas as matrículas de um aluno."""
    print("\n--- LISTAR MATRÍCULAS DO ALUNO ---")
    
    aluno_id = input_validado("ID do aluno: ", r"^\d+$", "ID inválido.")
    
    aluno = buscar_aluno_por_id(int(aluno_id))
    if not aluno:
        print("\n❌ Aluno não encontrado.")
        input("\nPressione ENTER para continuar...")
        return
    
    print(f"\nAluno: {aluno.nome_completo}")
    print("-" * 50)
    
    matriculas = listar_matriculas_aluno(int(aluno_id))
    
    if matriculas:
        for matricula in matriculas:
            print(f"  Modalidade: {matricula.modalidade.nome}")
            print(f"  Graduação: {matricula.graduacao}")
            print(f"  Número da Matrícula: {matricula.numero_matricula}")
            print("-" * 50)
    else:
        print("⚠️  Nenhuma matrícula encontrada.")
    
    input("\nPressione ENTER para continuar...")

def opcao_atualizar_graduacao() -> None:
    """Atualiza a graduação de um aluno em uma modalidade."""
    print("\n--- ATUALIZAR GRADUAÇÃO ---")
    
    aluno_id = input_validado("ID do aluno: ", r"^\d+$", "ID inválido.")
    
    aluno = buscar_aluno_por_id(int(aluno_id))
    if not aluno:
        print("\n❌ Aluno não encontrado.")
        input("\nPressione ENTER para continuar...")
        return
    
    print(f"\nAluno: {aluno.nome_completo}")
    
    matriculas = listar_matriculas_aluno(int(aluno_id))
    if not matriculas:
        print("⚠️  Este aluno não possui matrículas.")
        input("\nPressione ENTER para continuar...")
        return
    
    print("\nMatrículas do aluno:")
    for matricula in matriculas:
        print(f"  {matricula.modalidade.id} - {matricula.modalidade.nome} (Graduação: {matricula.graduacao})")
    
    modalidade_id = input_validado("\nID da modalidade: ", r"^\d+$", "ID inválido.")
    nova_graduacao = input_validado("Nova graduação: ")
    
    if atualizar_graduacao(int(aluno_id), int(modalidade_id), nova_graduacao):
        logging.info(f"Graduação do aluno {aluno_id} atualizada por {session_user.nome_usuario}")
    
    input("\nPressione ENTER para continuar...")

# ============================================================
# MENUS DE RELATÓRIOS
# ============================================================

@checar_permissao_decorator("VIEWER")
def menu_relatorios() -> None:
    """Menu de relatórios."""
    opcoes = {
        "1": opcao_relatorio_alunos_academia,
        "2": opcao_relatorio_alunos_modalidade,
        "0": lambda: None
    }
    
    while True:
        print("\n" + "-"*50)
        print("         MENU RELATÓRIOS")
        print("-"*50)
        print("1 - Alunos por Academia")
        print("2 - Alunos por Modalidade")
        print("0 - Voltar")
        print("-"*50)
        
        escolha = input("Escolha: ").strip()
        
        if escolha == "0":
            break
        elif escolha in opcoes:
            opcoes[escolha]()
        else:
            print("❌ Opção inválida.")
            input("\nPressione ENTER para continuar...")

def opcao_relatorio_alunos_academia() -> None:
    """Gera relatório de alunos por academia."""
    print("\n--- RELATÓRIO: ALUNOS POR ACADEMIA ---")
    
    contagem = contar_alunos_por_academia()
    
    if not contagem:
        print("⚠️  Nenhum dado disponível.")
        input("\nPressione ENTER para continuar...")
        return
    
    print()
    for nome_academia, total in contagem.items():
        print(f"  {nome_academia}: {total} aluno(s)")
    
    input("\nPressione ENTER para continuar...")

def opcao_relatorio_alunos_modalidade() -> None:
    """Gera relatório de alunos por modalidade."""
    print("\n--- RELATÓRIO: ALUNOS POR MODALIDADE ---")
    
    contagem = contar_alunos_por_modalidade_e_graduacao()
    
    if not contagem:
        print("⚠️  Nenhum dado disponível.")
        input("\nPressione ENTER para continuar...")
        return
    
    print()
    for modalidade_id, graduacoes in contagem.items():
        print(f"\nModalidade ID {modalidade_id}:")
        for graduacao, total in graduacoes.items():
            print(f"  {graduacao}: {total} aluno(s)")
    
    input("\nPressione ENTER para continuar...")

# ============================================================
# MENUS DE USUÁRIOS (APENAS ADMIN)
# ============================================================

@checar_permissao_decorator("ADMIN")
def menu_usuarios() -> None:
    """Menu de gerenciamento de usuários (apenas ADMIN)."""
    opcoes = {
        "1": opcao_registrar_usuario,
        "2": opcao_listar_usuarios,
        "3": opcao_atualizar_papel_usuario,
        "4": opcao_deletar_usuario,
        "0": lambda: None
    }
    
    while True:
        print("\n" + "-"*50)
        print("    MENU USUÁRIOS (ADMIN)")
        print("-"*50)
        print("1 - Registrar usuário")
        print("2 - Listar usuários")
        print("3 - Atualizar papel")
        print("4 - Deletar usuário")
        print("0 - Voltar")
        print("-"*50)
        
        escolha = input("Escolha: ").strip()
        
        if escolha == "0":
            break
        elif escolha in opcoes:
            opcoes[escolha]()
        else:
            print("❌ Opção inválida.")
            input("\nPressione ENTER para continuar...")

def opcao_registrar_usuario() -> None:
    """Registra um novo usuário no sistema."""
    print("\n--- REGISTRAR USUÁRIO ---")
    
    nome = input_validado("Nome de usuário: ")
    senha = input_validado("Senha: ")
    
    print("\nNíveis de acesso:")
    print("  ADMIN - Acesso total ao sistema")
    print("  EDITOR - Pode gerenciar dados mas não usuários")
    print("  VIEWER - Apenas visualização")
    
    papel = input_validado("Papel (ADMIN/EDITOR/VIEWER): ", r"^(ADMIN|EDITOR|VIEWER)$", "Papel inválido.")
    
    if registrar_usuario(nome, senha, papel):
        logging.info(f"Usuário {nome} registrado por {session_user.nome_usuario}")
    
    input("\nPressione ENTER para continuar...")

def opcao_listar_usuarios() -> None:
    """Lista todos os usuários do sistema."""
    print("\n--- LISTA DE USUÁRIOS ---")
    
    usuarios = listar_usuarios()
    
    if not usuarios:
        print("⚠️  Nenhum usuário cadastrado.")
        input("\nPressione ENTER para continuar...")
        return
    
    print(f"\nTotal de usuários: {len(usuarios)}\n")
    print(f"{'ID':<5} {'Nome de Usuário':<25} {'Papel':<15}")
    print("-" * 45)
    
    for usuario in usuarios:
        print(f"{usuario.id:<5} {usuario.nome_usuario[:24]:<25} {usuario.papel:<15}")
    
    input("\nPressione ENTER para continuar...")

def opcao_atualizar_papel_usuario() -> None:
    """Atualiza o papel de um usuário."""
    print("\n--- ATUALIZAR PAPEL DO USUÁRIO ---")
    
    usuarios = listar_usuarios()
    if not usuarios:
        print("⚠️  Nenhum usuário cadastrado.")
        input("\nPressione ENTER para continuar...")
        return
    
    print("\nUsuários disponíveis:")
    for usuario in usuarios:
        print(f"  {usuario.nome_usuario} ({usuario.papel})")
    
    nome = input_validado("\nNome do usuário: ")
    
    print("\nNovos papéis disponíveis:")
    print("  ADMIN - Acesso total")
    print("  EDITOR - Gerenciar dados")
    print("  VIEWER - Apenas visualização")
    
    novo_papel = input_validado("Novo papel (ADMIN/EDITOR/VIEWER): ", r"^(ADMIN|EDITOR|VIEWER)$", "Papel inválido.")
    
    if atualizar_papel_usuario(nome, novo_papel):
        logging.info(f"Papel do usuário {nome} atualizado para {novo_papel} por {session_user.nome_usuario}")
    
    input("\nPressione ENTER para continuar...")

def opcao_deletar_usuario() -> None:
    """Deleta um usuário do sistema."""
    print("\n--- DELETAR USUÁRIO ---")
    
    usuarios = listar_usuarios()
    if not usuarios:
        print("⚠️  Nenhum usuário cadastrado.")
        input("\nPressione ENTER para continuar...")
        return
    
    print("\nUsuários disponíveis:")
    for usuario in usuarios:
        print(f"  {usuario.nome_usuario} ({usuario.papel})")
    
    nome = input_validado("\nNome do usuário para deletar: ")
    
    if nome == session_user.nome_usuario:
        print("\n❌ Não é possível deletar o próprio usuário.")
        input("\nPressione ENTER para continuar...")
        return
    
    confirmacao = input("\n⚠️  Confirma a exclusão? (sim/não): ").strip().lower()
    
    if confirmacao == 'sim':
        if deletar_usuario(nome):
            logging.info(f"Usuário {nome} deletado por {session_user.nome_usuario}")
    else:
        print("\n❌ Exclusão cancelada.")
    
    input("\nPressione ENTER para continuar...")

# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================

def main() -> None:
    """Função principal do sistema."""
    try:
        inicializar_sistema()
        tela_de_login()
        menu_principal()
    except KeyboardInterrupt:
        print("\n\n⚠️  Sistema interrompido pelo usuário.")
        logging.info("Sistema interrompido via KeyboardInterrupt")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        logging.error(f"Erro crítico no sistema: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()