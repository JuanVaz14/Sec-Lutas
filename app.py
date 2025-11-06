# app.py - VERSÃO CORRIGIDA

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template_string, redirect, url_for, request, session, flash
from models import Session as DBSession, Academia, create_database_tables, Usuario
from academia_service import listar_todas_academias
from auth_service import autenticar_usuario, inicializar_usuario_admin
from aluno_service import listar_alunos_por_academia, cadastrar_aluno
import sys
import os

# Configuração do Flask
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback_secreto_caso_o_env_falhe')
ACADEMIA_ID_TESTE = 1

# Função auxiliar para checar permissão (CORRIGIDA)
def checar_permissao_web(papeis_permitidos):
    """Verifica se o usuário logado tem uma das permissões necessárias."""
    if 'usuario' not in session or 'papel' not in session:
        return False
    
    papel_usuario = session.get('papel', '').upper()
    
    # ADMIN tem acesso a tudo
    if papel_usuario == 'ADMIN':
        return True
    
    # Verifica se o papel do usuário está na lista de permitidos
    papeis_permitidos_upper = [p.upper() for p in papeis_permitidos]
    
    # EDITOR tem acesso a VIEWER também
    if papel_usuario == 'EDITOR' and 'VIEWER' in papeis_permitidos_upper:
        return True
    
    return papel_usuario in papeis_permitidos_upper

def render_page(title, body):
    """Template base simples para todas as páginas."""
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ title }}</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container { 
                max-width: 1000px; 
                margin: auto; 
                background: white; 
                padding: 30px; 
                border-radius: 15px; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            }
            h1 { 
                color: #667eea; 
                margin-bottom: 20px;
                font-size: 2em;
            }
            h2 { 
                border-bottom: 3px solid #667eea; 
                padding-bottom: 10px; 
                margin: 20px 0;
                color: #333;
            }
            .flash-error { 
                color: #721c24; 
                background-color: #f8d7da; 
                border: 1px solid #f5c6cb;
                padding: 12px; 
                border-radius: 5px; 
                margin-bottom: 15px; 
            }
            .flash-success { 
                color: #155724; 
                background-color: #d4edda; 
                border: 1px solid #c3e6cb;
                padding: 12px; 
                border-radius: 5px; 
                margin-bottom: 15px; 
            }
            nav { 
                margin-bottom: 25px; 
                border-bottom: 2px solid #667eea; 
                padding-bottom: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            nav a { 
                margin-right: 20px; 
                text-decoration: none; 
                color: #667eea;
                font-weight: 600;
                transition: color 0.3s;
            }
            nav a:hover {
                color: #764ba2;
            }
            .user-info {
                font-weight: 600;
                color: #333;
            }
            table { 
                border-collapse: collapse; 
                margin-top: 15px; 
                width: 100%;
            }
            th, td { 
                border: 1px solid #ddd; 
                padding: 12px; 
                text-align: left; 
            }
            th {
                background-color: #667eea;
                color: white;
                font-weight: 600;
            }
            tr:nth-child(even) {
                background-color: #f8f9fa;
            }
            input[type="text"], input[type="password"], input[type="date"] {
                width: 100%;
                padding: 10px;
                margin: 8px 0;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 1em;
            }
            input[type="submit"], .btn {
                padding: 12px 25px;
                background-color: #667eea;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1em;
                font-weight: 600;
                transition: background-color 0.3s;
                text-decoration: none;
                display: inline-block;
            }
            input[type="submit"]:hover, .btn:hover {
                background-color: #764ba2;
            }
            .btn-success {
                background-color: #28a745;
            }
            .btn-success:hover {
                background-color: #218838;
            }
            .btn-danger {
                background-color: #dc3545;
            }
            .btn-danger:hover {
                background-color: #c82333;
            }
            label {
                font-weight: 600;
                color: #333;
                display: block;
                margin-top: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            {% with messages = get_flashed_messages(with_categories=true) %}
              {% if messages %}
                {% for category, message in messages %}
                  <div class="flash-{{ category }}">{{ message }}</div>
                {% endfor %}
              {% endif %}
            {% endwith %}
            
            {% if session.get('usuario') %}
            <nav>
                <div>
                    <a href="{{ url_for('index') }}">🏠 Home</a>
                    <a href="{{ url_for('alunos_list') }}">👥 Alunos</a>
                    <a href="{{ url_for('relatorios') }}">📊 Relatórios</a>
                </div>
                <div class="user-info">
                    👤 {{ session['usuario'] }} ({{ session['papel'] }}) | 
                    <a href="{{ url_for('logout') }}">🚪 Sair</a>
                </div>
            </nav>
            {% endif %}

            {{ body | safe }}
        </div>
    </body>
    </html>
    """, title=title, body=body, session=session)


# Rota de Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        
        usuario_obj = autenticar_usuario(usuario, senha)
        
        if usuario_obj:
            session['usuario'] = usuario_obj.nome_usuario
            session['papel'] = usuario_obj.papel
            
            flash('Login bem-sucedido!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Credenciais inválidas.', 'error')
    
    form_html = """
    <h1>🔐 Acesso ao Sistema Web</h1>
    <form method="POST">
        <label for="usuario">Usuário:</label>
        <input type="text" id="usuario" name="usuario" required>
        
        <label for="senha">Senha:</label>
        <input type="password" id="senha" name="senha" required>
        
        <input type="submit" value="Entrar">
    </form>
    """
    return render_page("Login", form_html)


# Rota de Logout
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    session.pop('papel', None)
    flash('Você saiu do sistema.', 'success')
    return redirect(url_for('login'))


# Tela Principal / Home
@app.route('/')
def index():
    if not session.get('usuario'):
        flash('Você precisa fazer login para acessar.', 'error')
        return redirect(url_for('login'))
        
    if not checar_permissao_web(["ADMIN", "EDITOR", "VIEWER"]):
        flash('Permissão negada para acessar a Home.', 'error')
        return redirect(url_for('logout'))

    academias = listar_todas_academias()
    
    body_content = f"""
    <h1>🥋 Painel Principal - Secretaria de Lutas</h1>
    <p>Seu nível de acesso é: <strong>{session['papel']}</strong></p>
    
    <h2>📋 Menu de Opções</h2>
    <p>
        <a href="{url_for('alunos_list')}" class="btn">👥 Gerenciar Alunos (CRUD)</a>
        <a href="{url_for('relatorios')}" class="btn">📊 Relatórios</a>
    </p>

    <h2>🏢 Pólos Esportivos Cadastrados</h2>
    <table>
        <tr>
            <th>ID</th>
            <th>Nome</th>
            <th>Responsável</th>
        </tr>
        {''.join([f'<tr><td>{ac.id}</td><td><strong>{ac.nome}</strong></td><td>{ac.responsavel or "N/A"}</td></tr>' for ac in academias])}
    </table>
    """
    return render_page("Home - Maricá Esportes", body_content)


# Rotas de Alunos
@app.route('/alunos')
def alunos_list():
    if not checar_permissao_web(["ADMIN", "EDITOR"]):
        flash('PERMISSÃO NEGADA: Apenas ADMIN ou EDITOR podem gerenciar alunos.', 'error')
        return redirect(url_for('index'))
    
    alunos = listar_alunos_por_academia(ACADEMIA_ID_TESTE)
        
    body_content = f"""
    <h1>👥 Gerenciamento de Alunos</h1>
    <p>
        <a href="{url_for('alunos_adicionar')}" class="btn btn-success">➕ Adicionar Novo Aluno</a>
        <span style="margin-left: 20px;">Total de Alunos Ativos: <strong>{len(alunos)}</strong></span>
    </p>
    
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Nome Completo</th>
                <th>CPF</th>
                <th>Telefone</th>
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
                    <td>{aluno.telefone or "N/A"}</td>
                    <td>{'✅ ATIVO' if aluno.status_ativo else '❌ INATIVO'}</td>
                    <td>
                        <a href="{url_for('alunos_editar', id_aluno=aluno.id)}">✏️ Editar</a> | 
                        <a href="{url_for('alunos_remover', id_aluno=aluno.id)}" onclick="return confirm('Tem certeza que deseja remover {aluno.nome_completo}?')" class="btn-danger">🗑️ Remover</a>
                    </td>
                </tr>
            ''' for aluno in alunos])}
        </tbody>
    </table>
    """
    return render_page("Gerenciar Alunos", body_content)


@app.route('/alunos/adicionar', methods=['GET', 'POST'])
def alunos_adicionar():
    if not checar_permissao_web(["ADMIN", "EDITOR"]):
        flash('PERMISSÃO NEGADA: Apenas ADMIN ou EDITOR podem adicionar alunos.', 'error')
        return redirect(url_for('alunos_list'))

    if request.method == 'POST':
        try:
            nome = request.form['nome_completo']
            cpf = request.form['cpf']
            telefone = request.form.get('telefone', '')
            responsavel = request.form.get('responsavel', '')
            graduacao = request.form.get('graduacao', '')
            
            aluno_id = cadastrar_aluno(
                nome_completo=nome,
                cpf_limpo=cpf,
                academia_id=ACADEMIA_ID_TESTE,
                telefone=telefone,
                responsavel=responsavel,
                graduacao=graduacao
            )
            
            if aluno_id:
                flash(f"Aluno '{nome}' cadastrado com sucesso!", 'success')
                return redirect(url_for('alunos_list'))
            else:
                flash("Erro ao cadastrar aluno. Verifique se o CPF já existe.", 'error')
                
        except Exception as e:
            flash(f"Erro inesperado: {e}", 'error')
            
    body_content = f"""
    <h1>➕ Cadastrar Novo Aluno</h1>
    <p><a href="{url_for('alunos_list')}">← Voltar para a Lista de Alunos</a></p>
    
    <form method="POST">
        <label for="nome_completo">Nome Completo:</label>
        <input type="text" id="nome_completo" name="nome_completo" required>
        
        <label for="cpf">CPF (somente números - 11 dígitos):</label>
        <input type="text" id="cpf" name="cpf" required pattern="\\d{{11}}" title="O CPF deve ter 11 dígitos">
        
        <label for="telefone">Telefone:</label>
        <input type="text" id="telefone" name="telefone">

        <label for="responsavel">Responsável:</label>
        <input type="text" id="responsavel" name="responsavel">

        <label for="graduacao">Graduação Inicial:</label>
        <input type="text" id="graduacao" name="graduacao">
        
        <input type="submit" value="Cadastrar Aluno">
    </form>
    """
    return render_page("Cadastrar Aluno", body_content)


@app.route('/alunos/editar/<int:id_aluno>')
def alunos_editar(id_aluno):
    if not checar_permissao_web(["ADMIN", "EDITOR"]):
        flash('PERMISSÃO NEGADA.', 'error')
        return redirect(url_for('alunos_list'))
    
    body_content = f"<h2>Editar Aluno ID: {id_aluno}</h2><p>Lógica de Edição virá aqui.</p>"
    return render_page("Editar Aluno", body_content)
    
@app.route('/alunos/remover/<int:id_aluno>')
def alunos_remover(id_aluno):
    if not checar_permissao_web(["ADMIN"]):
        flash('PERMISSÃO NEGADA: Apenas ADMIN pode remover alunos.', 'error')
        return redirect(url_for('alunos_list'))
        
    from aluno_service import deletar_aluno
    if deletar_aluno(id_aluno):
        flash(f"Aluno ID {id_aluno} removido com sucesso.", 'success')
    else:
        flash(f"Erro ao remover aluno ID {id_aluno}.", 'error')
    
    return redirect(url_for('alunos_list'))


# Rota de Relatórios
@app.route('/relatorios')
def relatorios():
    if not checar_permissao_web(["ADMIN", "EDITOR", "VIEWER"]):
        flash('ACESSO NEGADO: Papel inválido.', 'error')
        return redirect(url_for('index'))
    
    body_content = "<h2>📊 Relatórios Gerenciais</h2><p>Página em construção! Aqui virão os relatórios.</p>"
    return render_page("Relatórios", body_content)


# Execução do Servidor
if __name__ == '__main__':
    create_database_tables()
    inicializar_usuario_admin()
    
    print("\n" + "="*50)
    print("🚀 Servidor Flask Iniciando")
    print("="*50)
    print("📍 Acesse: http://127.0.0.1:5000/login")
    print("👤 Usuário padrão: juan")
    print("🔑 Senha padrão: Lke74890@")
    print("="*50 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)