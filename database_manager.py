# No seu arquivo database_manager.py

from models import Academia, Aluno, Modalidade, Treinador, create_database_tables, Session
from datetime import date

if __name__ == '__main__':
    
    # 1. Cria ou atualiza as tabelas no DB (Modalidade e Treinador serão adicionadas)
    create_database_tables()
    
    session = Session()

    # --- População de Teste ---
    print("\n--- Iniciando População de Teste ---")

    # 2. Cria/Busca uma Academia base
    academia_nome = "Polo Esportivo de Inoã"
    nova_academia = session.query(Academia).filter_by(nome=academia_nome).first()
    
    if not nova_academia:
        nova_academia = Academia(
            nome=academia_nome, 
            endereco="Rua 1, Inoã", 
            responsavel="Prof. Carlos"
        )
        session.add(nova_academia)
        session.commit()
        print(f"Academia Criada: {nova_academia}")
    else:
        print(f"Academia Existente: {nova_academia}")
        
    # 3. Cria uma Modalidade
    nova_modalidade = Modalidade(nome="Jiu-Jitsu", tipo="Alto Rendimento")
    
    # Adiciona a modalidade APENAS se ela ainda não existir (unique=True)
    if not session.query(Modalidade).filter_by(nome=nova_modalidade.nome).first():
        session.add(nova_modalidade)
        session.commit()
        print(f"Modalidade Criada: {nova_modalidade}")
    else:
        # Se já existe, apenas a busca para usar na FK
        nova_modalidade = session.query(Modalidade).filter_by(nome=nova_modalidade.nome).first()
        print(f"Modalidade Existente: {nova_modalidade}")

    # 4. Adicionando um Aluno (usando seus dados de teste)
    novo_aluno = Aluno(
        nome_completo="Juan Pablo Vaz", 
        data_nascimento=date(2002, 10, 5), 
        cpf="19611319789", 
        academia_id=nova_academia.id
    )
    # Tenta adicionar o aluno, lida com erro se o CPF (unique) já existir
    if not session.query(Aluno).filter_by(cpf=novo_aluno.cpf).first():
        session.add(novo_aluno)
        session.commit()
        print(f"Aluno Adicionado: {novo_aluno}")
    else:
        print(f"Aluno (CPF {novo_aluno.cpf}) já existe. Pulando cadastro.")


    # 5. Adicionando um Treinador, vinculado à Academia e à Modalidade
    novo_treinador = Treinador(
        nome_completo="Maria de Souza", 
        telefone="987654321", 
        certificacao="Faixa Preta 1º Grau",
        academia_id=nova_academia.id, # Link para a Academia
        modalidade_id=nova_modalidade.id # Link para a Modalidade
    )
    session.add(novo_treinador)
    session.commit()
    print(f"Treinador Adicionado: {novo_treinador}")

    session.close()
    print("\n--- Testes Concluídos ---")

# No seu arquivo database_manager.py, abaixo do bloco de teste inicial:

from aluno_service import (
    cadastrar_aluno, 
    buscar_aluno_por_cpf, 
    listar_alunos_por_academia, 
    atualizar_status_aluno, 
    deletar_aluno
)

if __name__ == '__main__':
    # ... (Bloco de criação de tabelas e população inicial) ...
    
    # ----------------------------------------------------
    print("\n==============================================")
    print("        TESTANDO AS FUNÇÕES CRUD DE ALUNO")
    print("==============================================")
    
    session = Session()
    
    # Vamos buscar a Academia de teste criada anteriormente
    academia_teste = session.query(Academia).filter_by(nome="Polo Esportivo de Inoã").first()
    if not academia_teste:
        print("ERRO: Academia de teste não encontrada. Rode o bloco de criação inicial primeiro.")
        session.close()
        exit()
        
    session.close()
    
    # 1. CREATE: Cadastrando um novo aluno
    novo_aluno_teste = cadastrar_aluno(
        nome="Mariana Costa", 
        data_nasc="2003-05-15", # Formato ISO: YYYY-MM-DD
        cpf="11122233344", 
        academia_id=academia_teste.id
    )

    # 2. READ: Buscando o aluno
    print("\n--- Buscando Aluno ---")
    aluno_buscado = buscar_aluno_por_cpf("11122233344")
    if aluno_buscado:
        print(f"Encontrado: {aluno_buscado.nome_completo}, Status Ativo: {aluno_buscado.status_ativo}")

    # 3. UPDATE: Alterando o status
    print("\n--- Atualizando Status ---")
    atualizar_status_aluno(cpf="11122233344", status_ativo=False) # Agora Inativo

    # 4. READ (novamente) e Listar
    print("\n--- Listando Alunos Ativos na Academia ---")
    alunos_ativos = listar_alunos_por_academia(academia_teste.id)
    print(f"Total de alunos ativos encontrados: {len(alunos_ativos)}")
    for aluno in alunos_ativos:
        print(f"- {aluno.nome_completo}")

    # 5. DELETE: Removendo o aluno
    print("\n--- Deletando Aluno ---")
    deletar_aluno(cpf="11122233344")
    
    # Tentando buscar o aluno deletado
    if not buscar_aluno_por_cpf("11122233344"):
        print("Verificação: Aluno deletado com sucesso (Não encontrado após a deleção).")