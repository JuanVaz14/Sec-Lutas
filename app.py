# app.py

# --- Dependências ---
from dotenv import load_dotenv # Carrega variáveis de ambiente (como SECRET_KEY)
load_dotenv() 

from flask import Flask, render_template_string, redirect, url_for, request, session, flash, get_flashed_messages
from models import Session, Academia, create_database_tables, Usuario # Importa modelos necessários
from academia_service import listar_todas_academias
from auth_service import autenticar_usuario, inicializar_usuario_admin, checar_permissao
from aluno_service import (
    listar_alunos_por_academia, 
    cadastrar_aluno  # Função para adicionar alunos via web
)
import sys
import os

# --- Configuração do Flask ---
app = Flask(__name__)
# Carrega a chave do .env. É obrigatória para o login funcionar.
app.secret_key = os.environ.get('SECRET_KEY', 'fallback_secreto_caso_o_env_falhe') 
ACADEMIA_ID_TESTE = 1 # Usaremos o ID 1 para todos os testes CRUD

# --- Funções Auxiliares de HTML/UI ---

def render_page(title, body):
    # Template base simples para todas as páginas
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ title }}</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f4; }
            .container { max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0 0 0 / 10%); }
            h1 { color: #0066cc; }
            h2 { border-bottom: 2px solid #ccc; padding-bottom: 5px; }
            .flash-error { color: red; background-color: #ffe0e0; padding: 10px; border-radius: 4px; margin-bottom: 10px; }
            .flash-success { color: green; background-color: #e0ffe0; padding: 10px; border-radius: 4px; margin-bottom: 10px; }
            nav { margin-bottom: 20px; border-bottom: 1px solid #ccc; padding-bottom: 10px; }
            nav a { margin-right: 15px; text-decoration: none; color: #0066cc; }
            strong { font-weight: bold; }
            table { border-collapse: collapse; margin-top: 15px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 0.9em; }
        </style>
    </head>
    <body>
        <div class="container">
            {# Exibe mensagens de feedback (sucesso/erro) #}
            {% with messages = get_flashed_messages(with_categories=true) %}
              {% if messages %}
                {% for category, message in messages %}
                  <div class="flash-{{ category }}">{{ message }}</div>
                {% endfor %}
              {% endif %}
            {% endwith %}
            
            {# Menu de navegação superior, visível apenas se logado #}
            {% if session.get('usuario') %}
            <nav>
                <span>Logado como: <strong>{{ session['usuario'] }} ({{ session['papel'] }})</strong></span>
                <a href="{{ url_for('index') }}">Home</a>
                <a href="{{ url_for('alunos_list') }}">Alunos</a>
                <a href="{{ url_for('logout') }}">Sair</a>
            </nav>
            {% endif %}

            {{ body | safe }}  {# <--- FILTRO | safe #}
        </div>
    </body>
    </html>
    """, title=title, body=body, session=session, get_flashed_messages=get_flashed_messages)


# --- Rota de Login (Pública) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        
        if autenticar_usuario(usuario, senha):
            session_db = Session()
            usuario_obj = session_db.query(Usuario).filter_by(nome_usuario=usuario).one_or_none()
            session_db.close()
            
            if usuario_obj:
                session['usuario'] = usuario_obj.nome_usuario
                session['papel'] = usuario_obj.papel
                
                flash('Login bem-sucedido!', 'success')
                return redirect(url_for('index'))
            
        flash('Credenciais inválidas.', 'error')
    
    # Formulário de Login HTML (Limpo, sem dicas de senha ou usuário de teste)
    form_html = """
    <h1>Acesso ao Sistema Web</h1>
    <form method="POST">
        <label for="usuario">Usuário:</label><br>
        <input type="text" id="usuario" name="usuario" required style="width: 100%; padding: 8px; margin-bottom: 10px;"><br>
        
        <label for="senha">Senha:</label><br>
        <input type="password" id="senha" name="senha" required style="width: 100%; padding: 8px; margin-bottom: 20px;"><br>
        
        <input type="submit" value="Entrar" style="padding: 10px 15px; background-color: #0066cc; color: white; border: none; cursor: pointer;">
    </form>
    """
    return render_page("Login", form_html)


# --- Rota de Logout ---
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    session.pop('papel', None)
    flash('Você saiu do sistema.', 'success')
    return redirect(url_for('login'))


# --- Tela Principal / Home (Protegida) ---
@app.route('/')
def index():
    if not session.get('usuario'):
        flash('Você precisa fazer login para acessar.', 'error')
        return redirect(url_for('login'))
        
    if not checar_permissao(session['usuario'], ["ADMIN", "EDITOR", "VIEWER"]):
         flash('Permissão negada para acessar a Home.', 'error')
         return redirect(url_for('logout'))

    academias = listar_todas_academias()
    
    body_content = f"""
    <h2>Painel Principal</h2>
    <p>Seu nível de acesso é: <strong>{session['papel']}</strong>.</p>
    
    <h3>Menu de Opções</h3>
    <p>
        <a href="{url_for('alunos_list')}">Gerenciar Alunos (CRUD)</a><br>
        <a href="{url_for('relatorios')}">Relatórios (VIEWER)</a>
    </p>

    <h3>Pólos Esportivos Cadastrados</h3>
    <ul>
        {''.join([f'<li>ID: {ac.id} | Nome: <strong>{ac.nome}</strong> | Responsável: {ac.responsavel}</li>' for ac in academias])}
    </ul>
    """
    return render_page("Home - Maricá Esportes", body_content)


# --- Rotas de Alunos (Listagem e CRUD) ---

@app.route('/alunos')
def alunos_list():
    # Proteção de Acesso: Apenas ADMIN e EDITOR podem acessar CRUD
    if not checar_permissao(session.get('usuario'), ["ADMIN", "EDITOR"]):
        flash('PERMISSÃO NEGADA: Apenas ADMIN ou EDITOR podem gerenciar alunos.', 'error')
        return redirect(url_for('index'))
    
    alunos = listar_alunos_por_academia(ACADEMIA_ID_TESTE)
        
    # Conteúdo HTML para listar os alunos
    body_content = f"""
    <h2>Gerenciamento de Alunos</h2>
    <p><a href="{url_for('alunos_adicionar')}" style="padding: 5px 10px; background-color: green; color: white; text-decoration: none; border-radius: 3px;">+ Adicionar Novo Aluno</a> | Total de Alunos Ativos: {len(alunos)}</p>
    
    <table border="1" width="100%">
        <thead>
            <tr>
                <th>ID</th>
                <th>Nome Completo</th>
                <th>CPF</th>
                <th>Data Nasc.</th>
                <th>Status</th>
                <th>Ações</th>
            </tr>
        </thead>
        <tbody>
            {'' if alunos else '<tr><td colspan="6">Nenhum aluno ativo encontrado.</td></tr>'}
            {''.join([f'''
                <tr>
                    <td>{aluno.id}</td>
                    <td>{aluno.nome_completo}</td>
                    <td>{aluno.cpf_formatado}</td>
                    <td>{aluno.data_nascimento}</td>
                    <td>{'ATIVO' if aluno.status_ativo else 'INATIVO'}</td>
                    <td>
                        <a href="{url_for('alunos_editar', id_aluno=aluno.id)}">Editar</a> | 
                        <a href="{url_for('alunos_remover', cpf_aluno=aluno.cpf_formatado)}" onclick="return confirm('Tem certeza que deseja remover {aluno.nome_completo}? (Apenas ADMIN)')">Remover</a>
                    </td>
                </tr>
            ''' for aluno in alunos])}
        </tbody>
    </table>
    """
    return render_page("Gerenciar Alunos", body_content)


@app.route('/alunos/adicionar', methods=['GET', 'POST'])
def alunos_adicionar():
    # Proteção de Acesso
    if not checar_permissao(session.get('usuario'), ["ADMIN", "EDITOR"]):
        flash('PERMISSÃO NEGADA: Apenas ADMIN ou EDITOR podem adicionar alunos.', 'error')
        return redirect(url_for('alunos_list'))

    if request.method == 'POST':
        # --- LÓGICA DE CADASTRO DE ALUNO ---
        try:
            nome = request.form['nome_completo']
            cpf = request.form['cpf']
            rg = request.form['rg']
            data_nascimento = request.form['data_nascimento']
            telefone = request.form['telefone']
            
            aluno = cadastrar_aluno(
                nome_completo=nome,
                cpf=cpf,
                rg=rg,
                data_nascimento=data_nascimento,
                telefone=telefone,
                id_academia=ACADEMIA_ID_TESTE,
                status_ativo=True
            )
            
            if aluno:
                flash(f"Aluno '{aluno.nome_completo}' cadastrado com sucesso!", 'success')
                return redirect(url_for('alunos_list'))
            else:
                flash("Erro ao cadastrar aluno. Verifique o formato dos dados (ex: CPF/Data) ou se o CPF já existe.", 'error')
                
        except Exception as e:
            flash(f"Erro inesperado no formulário: {e}", 'error')
            
    # --- EXIBIÇÃO DO FORMULÁRIO HTML (GET) ---
    body_content = f"""
    <h2>Cadastrar Novo Aluno</h2>
    <p><a href="{url_for('alunos_list')}">← Voltar para a Lista de Alunos</a></p>
    
    <form method="POST">
        <label for="nome_completo">Nome Completo:</label><br>
        <input type="text" id="nome_completo" name="nome_completo" required style="width: 100%; padding: 8px; margin-bottom: 10px;"><br>
        
        <label for="cpf">CPF (somente números):</label><br>
        <input type="text" id="cpf" name="cpf" required pattern="\d{{11}}" title="O CPF deve ter 11 dígitos" style="width: 100%; padding: 8px; margin-bottom: 10px;"><br>
        
        <label for="rg">RG:</label><br>
        <input type="text" id="rg" name="rg" required style="width: 100%; padding: 8px; margin-bottom: 10px;"><br>

        <label for="data_nascimento">Data de Nascimento:</label><br>
        <input type="date" id="data_nascimento" name="data_nascimento" required style="width: 100%; padding: 8px; margin-bottom: 10px;"><br>
        
        <label for="telefone">Telefone:</label><br>
        <input type="text" id="telefone" name="telefone" required style="width: 100%; padding: 8px; margin-bottom: 20px;"><br>
        
        <input type="submit" value="Cadastrar Aluno" style="padding: 10px 15px; background-color: #0066cc; color: white; border: none; cursor: pointer;">
    </form>
    """
    return render_page("Cadastrar Aluno", body_content)


@app.route('/alunos/editar/<int:id_aluno>')
def alunos_editar(id_aluno):
    # Rota para o formulário de edição (Será implementado em seguida)
    if not checar_permissao(session.get('usuario'), ["ADMIN", "EDITOR"]):
        flash('PERMISSÃO NEGADA.', 'error')
        return redirect(url_for('alunos_list'))
    
    body_content = f"<h2>Editar Aluno ID: {id_aluno}</h2><p>Lógica de Edição virá aqui.</p>"
    return render_page("Editar Aluno", body_content)
    
@app.route('/alunos/remover/<cpf_aluno>')
def alunos_remover(cpf_aluno):
    # Rota de deleção (Apenas ADMIN)
    if not checar_permissao(session.get('usuario'), ["ADMIN"]):
        flash('PERMISSÃO NEGADA: Apenas ADMIN pode remover alunos.', 'error')
        return redirect(url_for('alunos_list'))
        
    # A lógica de deletar_aluno(cpf_aluno) virá aqui
    flash(f"Usuário com CPF {cpf_aluno} seria removido agora (Lógica de remoção pendente).", 'success')
    return redirect(url_for('alunos_list'))


# --- Rota de Relatórios (Permissão Mínima: VIEWERS) ---
@app.route('/relatorios')
def relatorios():
    if not checar_permissao(session.get('usuario'), ["ADMIN", "EDITOR", "VIEWER"]):
        flash('ACESSO NEGADO: Papel inválido.', 'error')
        return redirect(url_for('index'))
    
    body_content = "<h2>Relatórios Gerenciais</h2><p>Página em construção! Aqui virão os relatórios que você já criou.</p>"
    return render_page("Relatórios", body_content)


# --- Execução do Servidor (MUDANÇA AQUI!) ---
if __name__ == '__main__':
    # Garante que o BD exista e o usuário ADMIN (juan) esteja criado.
    create_database_tables()
    inicializar_usuario_admin() 
    
    print("--- Servidor Flask Iniciando ---")
    
    # 1. Descubra seu IP local (ex: 192.168.1.10)
    print("Acesse no seu navegador: http://127.0.0.1:5000/login")
    print("Para seu amigo acessar na mesma rede, use seu IP local (ex: http://0.0.0.0:5000/login)")
    
    # 2. Configura o Flask para ouvir todas as interfaces de rede (host='0.0.0.0')
    app.run(debug=True, host='0.0.0.0')