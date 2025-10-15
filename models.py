# models.py

from sqlalchemy import create_engine, Column, Integer, String, Date, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, date

# --- 1. Configuração do Banco de Dados ---

# Define o nome do arquivo do banco de dados SQLite
DATABASE_URL = "sqlite:///marica_esportes.db"

# Cria o objeto engine para conectar ao BD
engine = create_engine(DATABASE_URL)

# Cria a classe Base para as declarações dos modelos
Base = declarative_base()

# Cria o Session local
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- 2. Definição dos Modelos (Tabelas) ---

class Academia(Base):
    __tablename__ = 'academias'
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), unique=True, nullable=False)
    endereco = Column(String(255), nullable=False)
    responsavel = Column(String(100), nullable=True)
    
    # Relacionamento 1:N com Aluno (Uma academia tem muitos alunos)
    alunos = relationship("Aluno", back_populates="academia", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Academia(nome='{self.nome}', id={self.id})>"


class Modalidade(Base):
    __tablename__ = 'modalidades'
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50), unique=True, nullable=False)
    tipo = Column(String(50), nullable=True) # Ex: Base, Alto Rendimento
    
    # Relacionamento 1:N com Treinador (Uma modalidade tem muitos treinadores)
    treinadores = relationship("Treinador", back_populates="modalidade", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Modalidade(nome='{self.nome}')>"


class Aluno(Base):
    __tablename__ = 'alunos'
    
    id = Column(Integer, primary_key=True, index=True)
    nome_completo = Column(String(150), nullable=False)
    data_nascimento = Column(Date, nullable=False)
    cpf_formatado = Column(String(14), unique=True, nullable=False) # Ex: 000.000.000-00
    cpf_limpo = Column(String(11), unique=True, nullable=False, index=True) # Apenas números para busca
    status_ativo = Column(Boolean, default=True)
    data_cadastro = Column(Date, default=date.today)
    
    # Chave Estrangeira: Associa a Academia (Polo)
    academia_id = Column(Integer, ForeignKey('academias.id'), nullable=False)
    
    # Relacionamentos
    # N:1 com Academia
    academia = relationship("Academia", back_populates="alunos")
    
    # 1:N com Matrícula (Um aluno pode ter várias matrículas)
    matriculas = relationship("Matricula", back_populates="aluno", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Aluno(nome='{self.nome_completo}', cpf={self.cpf_limpo})>"


class Matricula(Base):
    __tablename__ = 'matriculas'
    
    id = Column(Integer, primary_key=True, index=True)
    numero_matricula = Column(String(50), unique=True, nullable=False)
    graduacao = Column(String(50), nullable=False) # Ex: Branca, Azul, Nível 1
    data_matricula = Column(Date, default=date.today)
    
    # Chaves Estrangeiras
    aluno_id = Column(Integer, ForeignKey('alunos.id'), nullable=False)
    modalidade_id = Column(Integer, ForeignKey('modalidades.id'), nullable=False)

    # Relacionamentos
    # N:1 com Aluno
    aluno = relationship("Aluno", back_populates="matriculas")
    # N:1 com Modalidade
    modalidade = relationship("Modalidade") 
    
    def __repr__(self):
        return f"<Matricula(num='{self.numero_matricula}', aluno_id={self.aluno_id})>"


class Treinador(Base):
    __tablename__ = 'treinadores'
    
    id = Column(Integer, primary_key=True, index=True)
    nome_completo = Column(String(150), nullable=False)
    telefone = Column(String(20), nullable=True)
    certificacao = Column(String(100), nullable=True)
    
    # Chaves Estrangeiras
    academia_id = Column(Integer, ForeignKey('academias.id'), nullable=False)
    modalidade_id = Column(Integer, ForeignKey('modalidades.id'), nullable=False)
    
    # Relacionamentos
    academia = relationship("Academia") # N:1 com Academia
    modalidade = relationship("Modalidade", back_populates="treinadores") # N:1 com Modalidade
    
    def __repr__(self):
        return f"<Treinador(nome='{self.nome_completo}', mod={self.modalidade_id})>"


class Usuario(Base):
    __tablename__ = 'usuarios'
    
    id = Column(Integer, primary_key=True, index=True)
    nome_usuario = Column(String(50), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    # Papel: ADMIN, EDITOR, VIEWER
    papel = Column(String(50), default="VIEWER", nullable=False) 
    
    def __repr__(self):
        return f"<Usuario(user='{self.nome_usuario}', papel='{self.papel}')>"


# --- 3. Função de Criação de Tabelas ---

def create_database_tables():
    """Cria todas as tabelas definidas em Base no banco de dados."""
    # O comando Base.metadata.create_all(engine) só cria as tabelas se elas não existirem
    Base.metadata.create_all(bind=engine)
    print("Banco de dados e tabelas criadas/atualizadas com sucesso!")

# Se você precisar rodar este script sozinho para criar o banco:
# if __name__ == '__main__':
#     create_database_tables()