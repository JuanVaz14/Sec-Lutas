# populate_test_data.py
from models import Session, Academia, create_database_tables
from aluno_service import cadastrar_aluno
from auth_service import inicializar_usuario_admin

def popular_dados_teste():
    print("🔧 Criando tabelas (se ainda não existirem)...")
    create_database_tables()
    inicializar_usuario_admin()
    
    session = Session()

    # Criar academias
    if not session.query(Academia).count():
        print("🏫 Inserindo academias de teste...")
        academias = [
            Academia(nome="Academia Maricá Fight", responsavel="Sensei João"),
            Academia(nome="Projeto Luta pela Vida", responsavel="Instrutora Ana"),
            Academia(nome="CT Guerreiro", responsavel="Professor Carlos"),
        ]
        session.add_all(academias)
        session.commit()
    else:
        print("✅ Academias já existem, pulando...")

    # Buscar academias
    academias = session.query(Academia).all()

    # Criar alunos de teste
    print("👥 Inserindo alunos fictícios...")
    alunos_teste = [
        ("Lucas Silva", "12345678901", "21999990000", "N/A", "Faixa Branca"),
        ("Maria Oliveira", "98765432100", "21988887777", "N/A", "Faixa Amarela"),
        ("Pedro Santos", "11122233344", "21977776666", "N/A", "Faixa Laranja"),
        ("Juliana Costa", "55566677788", "21966665555", "N/A", "Faixa Verde"),
        ("André Lima", "99988877766", "21955554444", "N/A", "Faixa Azul"),
    ]

    for i, (nome, cpf, tel, resp, grad) in enumerate(alunos_teste):
        academia = academias[i % len(academias)]
        try:
            cadastrar_aluno(
                nome_completo=nome,
                cpf_limpo=cpf,
                academia_id=academia.id,
                telefone=tel,
                responsavel=resp,
                graduacao=grad
            )
            print(f"✅ {nome} cadastrado em {academia.nome}")
        except Exception as e:
            print(f"⚠️ Erro ao cadastrar {nome}: {e}")

    session.close()
    print("\n🎉 Dados de teste inseridos com sucesso!")

if __name__ == "__main__":
    popular_dados_teste()
