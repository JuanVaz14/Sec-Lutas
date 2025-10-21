# main.py

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
    deletar_academia
)
from modalidade_treinador_service import (
    cadastrar_modalidade,
    listar_modalidades,
    cadastrar_treinador,
    listar_treinadores_por_modalidade,
    deletar_treinador
)
from matricula_service import (
    matricular_aluno,
    listar_matriculas_aluno,
    atualizar_graduacao
)
from relatorio_service import (
    contar_alunos_por_academia,
    contar_alunos_por_modalidade_e_graduacao
)
from auth_service import (
    autenticar_usuario, 
    inicializar_usuario_admin,
    registrar_usuario,
    checar_permissao,
    listar_usuarios,
    atualizar_papel_usuario,
    deletar_usuario
)
import sys
import re
from datetime import date 

# Variável global para armazenar o ID da Academia de teste
ACADEMIA_ID_TESTE = None 
# Variável global para armazenar o usuário logado
USUARIO_LOGADO = None

# --- Funções Auxiliares ---

def limpar_cpf(cpf: str) -> str:
    """Remove pontuação e retorna o CPF como string de 11 dígitos."""
    return re.sub(r'[^0-9]', '', cpf).zfill(11)

# --- Inicialização ---

def inicializar_sistema():
    """Garante que o banco de dados e as tabelas existam e configura a academia de teste e usuários."""
    global ACADEMIA_ID_TESTE
    
    print("--- Inicializando Sistema Secretaria de Lutas ---")
    
    # IMPORTANTE: Garante que as tabelas sejam criadas ANTES de qualquer consulta.
    create_database_tables() 
    
    # GARANTE A EXISTÊNCIA DE UMA ACADEMIA PARA TESTES
    session = Session()
    academia_teste = session.query(Academia).filter_by(nome="Polo Esportivo de Inoã").first()
    
    # Lógica de criação da academia de teste
    if not academia_teste:
        print("Criando Academia de Teste (Polo Esportivo de Inoã)...")
        try:
            academia_teste = Academia(id=1, nome="Polo Esportivo de Inoã", endereco="Rua X", responsavel="João da Silva")
            session.add(academia_teste)
            session.commit()
        except Exception:
             session.rollback()
             academia_teste = session.query(Academia).filter_by(nome="Polo Esportivo de Inoã").first() 
             if not academia_teste:
                 academia_teste = Academia(nome="Polo Esportivo de Inoã", endereco="Rua X", responsavel="João da Silva")
                 session.add(academia_teste)
                 session.commit()
    
    ACADEMIA_ID_TESTE = academia_teste.id
    session.close()
    
    print(f"ID da Academia de Teste: {ACADEMIA_ID_TESTE}")
    inicializar_usuario_admin() 
    print("---------------------------------------------")

# --- Telas de Login ---

def tela_de_login():
    """Loop de login que precede o menu principal."""
    global USUARIO_LOGADO
    MAX_TENTATIVAS = 3
    tentativas = 0
    
    session = Session()
    # Verifica se existe pelo menos um usuário no BD recém-criado
    if session.query(Usuario).count() == 0:
        print("\nALERTA: Nenhum usuário encontrado. Registre o primeiro usuário para acessar.")
        nome = input("Definir Novo Usuário: ")
        senha = input("Definir Nova Senha: ")
        # Garante a criação do ADMIN inicial, caso não exista
        registrar_usuario(nome, senha, papel="ADMIN") 
    session.close()

    while tentativas < MAX_TENTATIVAS:
        print("\n==============================================")
        print("          ACESSO RESTRITO - LOGIN")
        print("==============================================")
        
        usuario_input = input("Usuário: ")
        senha_input = input("Senha: ")
        
        if autenticar_usuario(usuario_input, senha_input):
            USUARIO_LOGADO = usuario_input 
            print(f"\nAcesso concedido. Bem-vindo {USUARIO_LOGADO}!")
            return True 
        else:
            tentativas += 1
            print(f"Credenciais inválidas. Tentativas restantes: {MAX_TENTATIVAS - tentativas}")
            
    print("\nNúmero máximo de tentativas excedido. Encerrando o sistema.")
    sys.exit(1)
    return False

# --- Menus de Navegação ---

def exibir_menu_principal():
    print("\n==============================================")
    print("      SISTEMA DE GESTÃO - SECRETARIA DE LUTAS")
    print("==============================================")
    print("1. Gerenciar Alunos")
    print("2. Gerenciar Academias/Polos")
    print("3. Gerenciar Modalidades e Treinadores")
    print("4. Gerenciar Matrículas e Graduações")
    print("5. Relatórios Gerenciais (VIEWER)")
    print("6. Gerenciar Usuários (ADMIN)") 
    print("9. Sair")
    print("----------------------------------------------")


def executar_menu_alunos():
    """Menu para CRUD de Alunos, incluindo a nova opção de detalhe por ID."""
    while True:
        print("\n[ GERENCIAMENTO DE ALUNOS ]")
        print("1. Cadastrar Novo Aluno")
        print("2. Listar TODOS os Alunos Cadastrados (Ativos/Inativos)") 
        print("3. Buscar Aluno por CPF")
        print("4. Mudar Status")
        print("5. Remover Aluno (ADMIN)") 
        print("9. Voltar ao Menu Principal")
        try:
            opcao = input("Escolha uma opção: ")
            
            if opcao == '1':
                print("\n--- CADASTRO ---")
                nome = input("Nome Completo: ")
                cpf_input = input("CPF (ex: 000.000.000-00): ")
                cpf_limpo = limpar_cpf(cpf_input)
                
                if len(cpf_limpo) != 11 or not cpf_limpo.isdigit():
                    print("ALERTA: CPF inválido. Certifique-se de que possui 11 dígitos numéricos.")
                    continue
                    
                data_nasc_str = input("Data de Nascimento (DD-MM-AAAA): ")
                
                cadastrar_aluno(nome, data_nasc_str, cpf_input, ACADEMIA_ID_TESTE)


            elif opcao == '2':
                alunos = listar_todos_alunos() 
                
                print(f"Total de Alunos Encontrados: {len(alunos)}")
                if alunos:
                    print("ID  | Status  | CPF            | Nome")
                    print("----|---------|-----------------|---------------------------------")
                    for aluno in alunos:
                        status_str = "ATIVO " if aluno.status_ativo else "INATIVO"
                        print(f"{aluno.id:<3} | {status_str:<7} | {aluno.cpf_formatado} | {aluno.nome_completo}")
                        
                    # ------------------------------------------------------------------
                    # FUNCIONALIDADE DE VISUALIZAÇÃO DE DETALHES POR ID
                    # ------------------------------------------------------------------
                    while True:
                        try:
                            id_aluno_detalhe = input("\n[DETALHES] Digite o ID do aluno para ver as informações (0 para voltar): ")
                            id_aluno_detalhe = int(id_aluno_detalhe)
                            
                            if id_aluno_detalhe == 0:
                                break
                                
                            aluno = buscar_aluno_por_id(id_aluno_detalhe) 
                            
                            if aluno:
                                print("\n--- INFORMAÇÕES COMPLETAS DO ALUNO ---")
                                print(f"  ID: {aluno.id}")
                                print(f"  Nome Completo: {aluno.nome_completo}")
                                print(f"  CPF: {aluno.cpf_formatado}")
                                print(f"  Data de Nascimento: {aluno.data_nascimento.strftime('%d/%m/%Y')}")
                                print(f"  Status: {'ATIVO' if aluno.status_ativo else 'INATIVO'}")
                                
                                # Detalhes da Academia
                                if aluno.academia:
                                    print(f"  Academia/Polo: {aluno.academia.nome} (ID: {aluno.academia_id})")
                                else:
                                    print("  Academia/Polo: Não associado")
                                    
                                # Detalhes das Matrículas
                                if aluno.matriculas:
                                    print("  --- MATRÍCULAS ---")
                                    for mat in aluno.matriculas:
                                        print(f"    - Nº: {mat.numero_matricula} | Modalidade: {mat.modalidade.nome} | Graduação: {mat.graduacao}")
                                else:
                                    print("  Matrículas: Nenhuma")
                                print("--------------------------------------")
                            else:
                                print(f"ERRO: Aluno com ID {id_aluno_detalhe} não encontrado.")
                                
                        except ValueError:
                            print("Entrada inválida. Por favor, digite um número inteiro.")
                        except Exception as e:
                            print(f"Ocorreu um erro ao buscar detalhes: {e}")
                    # ------------------------------------------------------------------
                else:
                    print("Nenhum aluno cadastrado no banco de dados.")

            elif opcao == '3':
                cpf_busca = input("Digite o CPF para busca: ")
                aluno = buscar_aluno_por_cpf(cpf_busca)
                if aluno:
                    print(f"  Encontrado: {aluno.nome_completo} | Status: {'ATIVO' if aluno.status_ativo else 'INATIVO'} | Academia: {aluno.academia.nome}")
                else:
                    print(f"  Aluno com CPF {limpar_cpf(cpf_busca)} não encontrado.")

            elif opcao == '4':
                cpf_busca = input("CPF do aluno: ")
                novo_status = input("Novo Status (A para Ativo / I para Inativo): ").upper()
                atualizar_status_aluno(cpf_busca, True if novo_status == 'A' else False)
            
            elif opcao == '5':
                PAPEIS_PERMITIDOS = ["ADMIN"] 
                if not checar_permissao(USUARIO_LOGADO, PAPEIS_PERMITIDOS):
                    print("PERMISSÃO NEGADA: Apenas ADMIN pode remover alunos.")
                    continue
                cpf_busca = input("CPF do aluno que deseja remover: ")
                deletar_aluno(cpf_busca)

            elif opcao == '9':
                break
                
            else:
                print("Opção inválida. Tente novamente.")

        except Exception as e:
            print(f"Ocorreu um erro: {e}")


def executar_menu_academias():
    """Menu para CRUD de Academias. Deleção restrita a ADMIN."""
    while True:
        print("\n[ GERENCIAMENTO DE ACADEMIAS/POLOS ]")
        print("1. Cadastrar Novo Polo")
        print("2. Listar Todos os Polos")
        print("3. Atualizar Endereço/Responsável")
        print("4. Remover Polo (ADMIN)")
        print("9. Voltar ao Menu Principal")
        try:
            opcao = input("Escolha uma opção: ")
            
            if opcao == '1':
                nome = input("Nome do Polo/Academia: ")
                endereco = input("Endereço Completo: ")
                responsavel = input("Nome do Responsável: ")
                cadastrar_academia(nome, endereco, responsavel)

            elif opcao == '2':
                academias = listar_todas_academias()
                print(f"Total de Polos Cadastrados: {len(academias)}")
                for ac in academias:
                    print(f"  ID: {ac.id} | Nome: {ac.nome} | Responsável: {ac.responsavel}")

            elif opcao == '3':
                ac_id = int(input("ID do Polo que deseja atualizar: "))
                novo_end = input("Novo Endereço (Vazio para não alterar): ")
                novo_resp = input("Novo Responsável (Vazio para não alterar): ")
                
                atualizar_academia(ac_id, endereco=novo_end or None, responsavel=novo_resp or None)
            
            elif opcao == '4':
                PAPEIS_PERMITIDOS = ["ADMIN"] 
                if not checar_permissao(USUARIO_LOGADO, PAPEIS_PERMITIDOS):
                    print("PERMISSÃO NEGADA: Apenas ADMIN pode remover polos/academias.")
                    continue
                ac_id = int(input("ID do Polo que deseja remover: "))
                deletar_academia(ac_id)

            elif opcao == '9':
                break
                
            else:
                print("Opção inválida. Tente novamente.")

        except ValueError:
            print("Entrada inválida. Digite números onde solicitado.")
        except Exception as e:
            print(f"Ocorreu um erro: {e}")


def executar_menu_modalidades_treinadores():
    """Menu para CRUD de Modalidades e Treinadores. Deleção restrita a ADMIN."""
    while True:
        print("\n[ GERENCIAMENTO DE MODALIDADES E TREINADORES ]")
        print("1. Cadastrar Modalidade")
        print("2. Listar Modalidades")
        print("3. Cadastrar Treinador")
        print("4. Listar Treinadores por Modalidade")
        print("5. Remover Treinador (ADMIN)")
        print("9. Voltar ao Menu Principal")
        try:
            opcao = input("Escolha uma opção: ")
            
            if opcao == '1':
                nome = input("Nome da Modalidade: ")
                tipo = input("Tipo (ex: Base, Alto Rendimento): ")
                cadastrar_modalidade(nome, tipo)

            elif opcao == '2':
                modalidades = listar_modalidades()
                print(f"Total de Modalidades: {len(modalidades)}")
                for mod in modalidades:
                    print(f"  ID: {mod.id} | Nome: {mod.nome} | Tipo: {mod.tipo}")

            elif opcao == '3':
                nome = input("Nome do Treinador: ")
                telefone = input("Telefone: ")
                certificacao = input("Certificação: ")
                
                listar_modalidades()
                modalidade_id = int(input("ID da Modalidade que irá treinar: "))
                academia_id = int(input(f"ID da Academia (ex: {ACADEMIA_ID_TESTE}): "))
                
                cadastrar_treinador(nome, telefone, certificacao, academia_id, modalidade_id)

            elif opcao == '4':
                listar_modalidades()
                mod_id = int(input("ID da Modalidade para listar treinadores: "))
                treinadores = listar_treinadores_por_modalidade(mod_id)
                if treinadores:
                    for t in treinadores:
                        print(f"  ID: {t.id} | Nome: {t.nome_completo} | Cert.: {t.certificacao}")
                else:
                    print(f"Nenhum treinador encontrado para a modalidade ID {mod_id}.")
            
            elif opcao == '5':
                PAPEIS_PERMITIDOS = ["ADMIN"] 
                if not checar_permissao(USUARIO_LOGADO, PAPEIS_PERMITIDOS):
                    print("PERMISSÃO NEGADA: Apenas ADMIN pode remover treinadores.")
                    continue
                treinador_id = int(input("ID do Treinador que deseja remover: "))
                deletar_treinador(treinador_id)

            elif opcao == '9':
                break
                
            else:
                print("Opção inválida. Tente novamente.")

        except ValueError:
            print("Entrada inválida. Digite números onde solicitado.")
        except Exception as e:
            print(f"Ocorreu um erro: {e}")


def executar_menu_matriculas():
    """Função para rodar o menu específico de Matrículas."""
    while True:
        print("\n[ GERENCIAMENTO DE MATRÍCULAS/GRADUAÇÕES ]")
        print("1. Matricular Aluno em Modalidade")
        print("2. Listar Matrículas do Aluno")
        print("3. Atualizar Graduação (Faixa/Nível)")
        print("9. Voltar ao Menu Principal")
        try:
            opcao = input("Escolha uma opção: ")
            
            if opcao == '1':
                print("\n--- MATRICULAR ALUNO ---")
                
                aluno_id = int(input("ID do Aluno: "))
                modalidades = listar_modalidades()
                print("Modalidades disponíveis:")
                for mod in modalidades:
                    print(f"  ID: {mod.id} | Nome: {mod.nome}")
                
                modalidade_id = int(input("ID da Modalidade: "))
                
                num_matr = input("Número da Matrícula (Único): ")
                grad_inicial = input("Graduação Inicial (ex: Branca, Iniciante): ")
                
                matricular_aluno(aluno_id, modalidade_id, num_matr, grad_inicial)

            elif opcao == '2':
                print("\n--- LISTAR MATRÍCULAS ---")
                aluno_id = int(input("ID do Aluno para listar as matrículas: "))
                
                matriculas = listar_matriculas_aluno(aluno_id)
                if matriculas:
                    print(f"Matrículas encontradas para o Aluno ID {aluno_id}:")
                    for m in matriculas:
                        print(f"  > Matrícula: {m.numero_matricula} | Modalidade: {m.modalidade.nome} | Graduação: {m.graduacao}")
                else:
                    print(f"Nenhuma matrícula encontrada para o Aluno ID {aluno_id}.")

            elif opcao == '3':
                print("\n--- ATUALIZAR GRADUAÇÃO ---")
                aluno_id = int(input("ID do Aluno: "))
                modalidade_id = int(input("ID da Modalidade para atualizar: "))
                nova_graduacao = input("Nova Graduação (ex: Faixa Azul, Nível 2): ")
                
                atualizar_graduacao(aluno_id, modalidade_id, nova_graduacao)

            elif opcao == '9':
                break
                
            else:
                print("Opção inválida. Tente novamente.")

        except ValueError:
            print("Entrada inválida. Certifique-se de digitar números onde solicitado.")
        except Exception as e:
            print(f"Ocorreu um erro: {e}")


def executar_menu_relatorios():
    """Menu para geração de relatórios gerenciais (acessível a todos)."""
    while True:
        print("\n[ RELATÓRIOS GERENCIAIS ]")
        print("1. Contagem de Alunos Ativos por Academia")
        print("2. Listar Alunos por Modalidade e Graduação")
        print("9. Voltar ao Menu Principal")
        
        try:
            opcao = input("Escolha uma opção: ")

            if opcao == '1':
                print("\n--- RELATÓRIO: ALUNOS POR ACADEMIA ---")
                resultados = contar_alunos_por_academia()
                if resultados:
                    for academia, total in resultados.items():
                        print(f"  > {academia}: {total} alunos ativos")
                else:
                    print("Nenhuma academia com alunos ativos encontrada.")
                    
            elif opcao == '2':
                print("\n--- RELATÓRIO: ALUNOS POR GRADUAÇÃO ---")
                modalidades = listar_modalidades()
                print("Modalidades disponíveis:")
                for mod in modalidades:
                    print(f"  - {mod.nome}")
                    
                nome_modalidade = input("Nome da Modalidade: ")
                graduacao_alvo = input("Graduação (Faixa/Nível) a ser buscada: ")
                
                alunos = contar_alunos_por_modalidade_e_graduacao(nome_modalidade, graduacao_alvo)
                
                if alunos:
                    print(f"Total de {len(alunos)} alunos encontrados em '{nome_modalidade}' ({graduacao_alvo}):")
                    for aluno in alunos:
                        print(f"  > Matrícula: {aluno['matricula']} | Aluno: {aluno['nome_aluno']} | Polo: {aluno['academia']}")
                else:
                    print("Nenhum aluno encontrado com esses critérios.")

            elif opcao == '9':
                break
                
            else:
                print("Opção inválida. Tente novamente.")

        except Exception as e:
            print(f"Ocorreu um erro no relatório: {e}")


def executar_menu_usuarios():
    """Menu para CRUD de Usuários (Acesso Restrito a ADMIN)."""
    global USUARIO_LOGADO
    
    PAPEIS_PERMITIDOS = ["ADMIN"]
    if not checar_permissao(USUARIO_LOGADO, PAPEIS_PERMITIDOS):
        print("\nPERMISSÃO NEGADA: Apenas administradores podem gerenciar usuários.")
        return

    while True:
        print("\n[ GERENCIAMENTO DE USUÁRIOS (ADMIN) ]")
        print("1. Listar Usuários")
        print("2. Registrar Novo Usuário")
        print("3. Alterar Nível de Acesso (Papel)")
        print("4. Excluir Usuário")
        print("9. Voltar ao Menu Principal")
        
        try:
            opcao = input("Escolha uma opção: ")

            if opcao == '1':
                print("\n--- LISTA DE USUÁRIOS ---")
                usuarios = listar_usuarios()
                for u in usuarios:
                    print(f"  > ID: {u.id} | Usuário: {u.nome_usuario} | Papel: {u.papel}")
                    
            elif opcao == '2':
                print("\n--- NOVO USUÁRIO ---")
                nome = input("Nome de Usuário: ")
                senha = input("Senha: ")
                papel = input("Papel (ADMIN, EDITOR ou VIEWER, [VIEWER] padrão): ") or "VIEWER"
                registrar_usuario(nome, senha, papel)
                
            elif opcao == '3':
                print("\n--- ALTERAR NÍVEL DE ACESSO ---")
                nome = input("Usuário para alterar: ")
                novo_papel = input("Novo Papel (ADMIN, EDITOR ou VIEWER): ")
                atualizar_papel_usuario(nome, novo_papel)
                
            elif opcao == '4':
                print("\n--- EXCLUIR USUÁRIO ---")
                nome = input("Usuário para excluir: ")
                if nome == USUARIO_LOGADO:
                     print("ERRO: Você não pode excluir sua própria conta enquanto está logado.")
                     continue
                deletar_usuario(nome)

            elif opcao == '9':
                break
                
            else:
                print("Opção inválida. Tente novamente.")

        except Exception as e:
            print(f"Ocorreu um erro no menu de usuários: {e}")


# --- Execução Principal ---

if __name__ == '__main__':
    
    inicializar_sistema()
    
    # --------------------------------------------------------------------------------------
    # O BLOCO DE TESTE DE INTEGRIDADE DO BD FOI REMOVIDO PARA PRODUÇÃO
    # --------------------------------------------------------------------------------------

    # O sistema de login é a primeira coisa a ser executada
    if tela_de_login():
        
        PAPEIS_CRUD = ["ADMIN", "EDITOR"]
        
        while True:
            exibir_menu_principal()
            try:
                escolha = input("Escolha uma opção: ")
                
                if escolha in ['1', '2', '3', '4', '6']:
                    if not checar_permissao(USUARIO_LOGADO, PAPEIS_CRUD):
                        print("\nACESSO NEGADO: Sua permissão é apenas de Visualizador (Opção 5).")
                        continue

                if escolha == '1':
                    executar_menu_alunos()
                elif escolha == '2':
                    executar_menu_academias() 
                elif escolha == '3':
                    executar_menu_modalidades_treinadores()
                elif escolha == '4':
                    executar_menu_matriculas()
                elif escolha == '5':
                    executar_menu_relatorios() 
                elif escolha == '6':
                    executar_menu_usuarios()
                elif escolha == '9':
                    print("\nEncerrando sistema. Até mais!")
                    sys.exit(0)
                else:
                    print("Opção inválida. Digite 1, 2, 3, 4, 5, 6 ou 9.")
                    
            except KeyboardInterrupt:
                print("\nEncerrando sistema. Até mais!")
                sys.exit(0)
            except Exception as e:
                print(f"Erro inesperado no menu principal: {e}")