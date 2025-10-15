from sqlalchemy import create_engine, Column, Integer, String, Date, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.schema import UniqueConstraint # Para garantir a unicidade da matrícula

# 1. Base Declarativa
Base = declarative_base()

# --- Configuração da Conexão e Sessão ---
engine = create_engine('sqlite:///marica_esportes.db')
Session = sessionmaker(bind=engine)

def create_database_tables():
    """Cria ou atualiza todas as tabelas no banco de dados SQLite."""
    Base.metadata.create_all(engine)
    print("Banco de dados e tabelas criadas/atualizadas com sucesso!")


# =========================================================================
# 2. Tabela de ACADEMIAS / POLOS DE TREINAMENTO
# =========================================================================
class Academia(Base):
    __tablename__ = 'academias'
    id = Column(Integer, primary_key=True)
    nome = Column(String)
    endereco = Column(String)
    responsavel = Column(String)
    
    alunos = relationship("Aluno", back_populates="academia") 

    def __repr__(self):
        return f"<Academia(id={self.id}, nome='{self.nome}')>"


# =========================================================================
# 3. Tabela de MATRÍCULA E GRADUAÇÃO (Tabela de Ligação Aluno <-> Modalidade)
# =========================================================================
class MatriculaModalidade(Base):
    __tablename__ = 'matriculas_modalidades'
    
    # ID primária da tabela de associação
    id = Column(Integer, primary_key=True) 
    
    # Colunas de Chave Estrangeira
    aluno_id = Column(Integer, ForeignKey('alunos.id'))
    modalidade_id = Column(Integer, ForeignKey('modalidades.id'))
    
    # Novas colunas de dados específicos da matrícula
    numero_matricula = Column(String, unique=True) # Ex: M-JJ-2024-001
    data_inicio = Column(Date)
    graduacao = Column(String, default="Iniciante") # Ex: Faixa Branca, Faixa Azul, Nível 1
    
    # Relações (para acessar os dados do Aluno e da Modalidade)
    aluno = relationship("Aluno", back_populates="matriculas_modalidades")
    modalidade = relationship("Modalidade", back_populates="matriculas_modalidades")
    
    # Restrição de unicidade: Um aluno não pode ter duas matrículas na mesma modalidade
    __table_args__ = (UniqueConstraint('aluno_id', 'modalidade_id', name='_aluno_modalidade_uc'),)

    def __repr__(self):
        return f"<Matricula(matr='{self.numero_matricula}', aluno_id={self.aluno_id}, mod_id={self.modalidade_id})>"


# =========================================================================
# 4. Tabela de ALUNOS (ATLETAS)
# =========================================================================
class Aluno(Base):
    __tablename__ = 'alunos'
    id = Column(Integer, primary_key=True)
    nome_completo = Column(String)
    data_nascimento = Column(Date)
    cpf = Column(String, unique=True) 
    status_ativo = Column(Boolean, default=True)
    academia_id = Column(Integer, ForeignKey('academias.id'))
    
    academia = relationship("Academia", back_populates="alunos")
    
    # NOVA RELAÇÃO: Permite acessar todas as matrículas do aluno
    matriculas_modalidades = relationship("MatriculaModalidade", back_populates="aluno")
    
    @property
    def cpf_formatado(self):
        """Retorna o CPF no formato 000.000.000-00 para exibição."""
        if self.cpf and len(self.cpf) == 11 and self.cpf.isdigit():
            return f"{self.cpf[:3]}.{self.cpf[3:6]}.{self.cpf[6:9]}-{self.cpf[9:]}"
        return self.cpf 

    def __repr__(self):
        return f"<Aluno(nome='{self.nome_completo}', CPF='{self.cpf_formatado}')>"


# =========================================================================
# 5. Tabela de MODALIDADES (LUTAS / ESPORTES)
# =========================================================================
class Modalidade(Base):
    __tablename__ = 'modalidades'
    id = Column(Integer, primary_key=True)
    nome = Column(String, unique=True)
    tipo = Column(String) 

    treinadores = relationship("Treinador", back_populates="modalidade")
    
    # NOVA RELAÇÃO: Permite acessar todos os alunos matriculados nesta modalidade
    matriculas_modalidades = relationship("MatriculaModalidade", back_populates="modalidade")

    def __repr__(self):
        return f"<Modalidade(id={self.id}, nome='{self.nome}')>"


# =========================================================================
# 6. Tabela de TREINADORES / PROFESSORES
# =========================================================================
class Treinador(Base):
    __tablename__ = 'treinadores'
    id = Column(Integer, primary_key=True)
    nome_completo = Column(String)
    telefone = Column(String)
    certificacao = Column(String)
    
    academia_id = Column(Integer, ForeignKey('academias.id'))
    modalidade_id = Column(Integer, ForeignKey('modalidades.id'))
    
    academia = relationship("Academia")
    modalidade = relationship("Modalidade", back_populates="treinadores")

    def __repr__(self):
        return f"<Treinador(nome='{self.nome_completo}', modalidade_id={self.modalidade_id})>"
    
# =========================================================================
# 7. Tabela de USUÁRIOS (Para Login e Permissão)
# =========================================================================
class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True)
    nome_usuario = Column(String, unique=True, nullable=False)
    # A senha será armazenada como um hash bcrypt (bytes)
    senha_hash = Column('senha_hash', String) 
    # CAMPO DE PERMISSÃO: Define o nível de acesso (ADMIN, EDITOR, VIEWER)
    papel = Column(String, default="VIEWER") 

    def __repr__(self):
        return f"<Usuario(nome='{self.nome_usuario}', papel='{self.papel}')>"

# ... (código posterior, incluindo a função create_database_tables) ...