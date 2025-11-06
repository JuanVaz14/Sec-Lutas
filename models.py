# models.py

from sqlalchemy import create_engine, Column, Integer, String, Date, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import date

# ===========================
# CONFIGURAÇÃO DO BANCO DE DADOS
# ===========================
DATABASE_URL = "sqlite:///sec_lutas.db"
engine = create_engine(DATABASE_URL, echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)


# ===========================
# TABELA: ACADEMIA (POLOS)
# ===========================
class Academia(Base):
    __tablename__ = 'academias'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(200), nullable=False, unique=True)
    endereco = Column(String(300), nullable=True)
    responsavel = Column(String(200), nullable=True)
    
    # Relacionamentos
    alunos = relationship("Aluno", back_populates="academia", cascade="all, delete-orphan")
    treinadores = relationship("Treinador", back_populates="academia", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Academia(id={self.id}, nome='{self.nome}')>"


# ===========================
# TABELA: ALUNO
# ===========================
class Aluno(Base):
    __tablename__ = 'alunos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_completo = Column(String(200), nullable=False)
    cpf_limpo = Column(String(11), unique=True, nullable=False)  # Somente números
    cpf_formatado = Column(String(14), nullable=True)  # 000.000.000-00
    data_nascimento = Column(Date, nullable=True)
    data_cadastro = Column(Date, default=date.today)
    telefone = Column(String(20), nullable=True)
    responsavel = Column(String(200), nullable=True)
    graduacao = Column(String(100), nullable=True)
    status_ativo = Column(Boolean, default=True)
    
    # Chave estrangeira
    academia_id = Column(Integer, ForeignKey('academias.id'), nullable=False)
    
    # Relacionamentos
    academia = relationship("Academia", back_populates="alunos")
    matriculas = relationship("Matricula", back_populates="aluno", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Aluno(id={self.id}, nome='{self.nome_completo}', cpf='{self.cpf_formatado}')>"


# ===========================
# TABELA: MODALIDADE
# ===========================
class Modalidade(Base):
    __tablename__ = 'modalidades'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False, unique=True)
    tipo = Column(String(100), nullable=True)  # Ex: "Alto Rendimento", "Base"
    
    # Relacionamentos
    treinadores = relationship("Treinador", back_populates="modalidade", cascade="all, delete-orphan")
    matriculas = relationship("Matricula", back_populates="modalidade", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Modalidade(id={self.id}, nome='{self.nome}')>"


# ===========================
# TABELA: TREINADOR
# ===========================
class Treinador(Base):
    __tablename__ = 'treinadores'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_completo = Column(String(200), nullable=False)
    telefone = Column(String(20), nullable=True)
    certificacao = Column(String(200), nullable=True)
    
    # Chaves estrangeiras
    academia_id = Column(Integer, ForeignKey('academias.id'), nullable=False)
    modalidade_id = Column(Integer, ForeignKey('modalidades.id'), nullable=False)
    
    # Relacionamentos
    academia = relationship("Academia", back_populates="treinadores")
    modalidade = relationship("Modalidade", back_populates="treinadores")
    
    def __repr__(self):
        return f"<Treinador(id={self.id}, nome='{self.nome_completo}')>"


# ===========================
# TABELA: MATRÍCULA (Aluno + Modalidade)
# ===========================
class Matricula(Base):
    __tablename__ = 'matriculas'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_matricula = Column(String(50), unique=True, nullable=False)
    graduacao = Column(String(100), nullable=True)
    data_matricula = Column(Date, default=date.today)
    
    # Chaves estrangeiras
    aluno_id = Column(Integer, ForeignKey('alunos.id'), nullable=False)
    modalidade_id = Column(Integer, ForeignKey('modalidades.id'), nullable=False)
    
    # Relacionamentos
    aluno = relationship("Aluno", back_populates="matriculas")
    modalidade = relationship("Modalidade", back_populates="matriculas")
    
    def __repr__(self):
        return f"<Matricula(id={self.id}, numero='{self.numero_matricula}')>"


# ===========================
# TABELA: USUÁRIO (Sistema de Login)
# ===========================
class Usuario(Base):
    __tablename__ = 'usuarios'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_usuario = Column(String(100), unique=True, nullable=False)
    senha_hash = Column(String(200), nullable=False)
    papel = Column(String(20), default="VIEWER")  # ADMIN, EDITOR, VIEWER
    
    def __repr__(self):
        return f"<Usuario(id={self.id}, usuario='{self.nome_usuario}', papel='{self.papel}')>"


# ===========================
# FUNÇÃO: CRIAR TABELAS
# ===========================
def create_database_tables():
    """Cria todas as tabelas no banco de dados se não existirem."""
    Base.metadata.create_all(engine)
    print("✅ Tabelas criadas/verificadas com sucesso!")
