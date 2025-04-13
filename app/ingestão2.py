from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date, ForeignKey, Float, Text
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.sql import text  # Importar text para executar comandos SQL brutos
import random

# String de conexão para o banco de dados
connection_string = 'postgresql+psycopg2://meu_usuario:minha_senha@192.168.183.1/postgres'
# Criar o engine
engine = create_engine(connection_string)

# Criar o session maker
Session = sessionmaker(bind=engine)

# Criar a classe base para os modelos
Base = declarative_base()

# Definir o modelo da tabela 'regiao_administrativa'
class RegiaoAdministrativa(Base):
    __tablename__ = 'regiao_administrativa'
    id_regiao = Column(Integer, primary_key=True)
    nome = Column(String(255), nullable=False)
    estado = Column(String(2), nullable=False)

# Definir o modelo da tabela 'endereco'
class Endereco(Base):
    __tablename__ = 'endereco'
    id_endereco = Column(Integer, primary_key=True)
    logradouro = Column(String(255), nullable=True)
    numero = Column(String(10), nullable=True)
    complemento = Column(String(255), nullable=True)
    bairro = Column(String(255), nullable=True)
    cidade = Column(String(255), nullable=True)
    estado = Column(String(2), nullable=True)
    cep = Column(String(10), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    id_regiao = Column(Integer, ForeignKey('regiao_administrativa.id_regiao'))

# Definir o modelo da tabela 'escola'
class Escola(Base):
    __tablename__ = 'escola'
    id_escola = Column(Integer, primary_key=True)
    nome = Column(String(255), nullable=False)
    id_endereco = Column(Integer, ForeignKey('endereco.id_endereco'))

    endereco = relationship('Endereco', backref='escolas')

# Definir o modelo da tabela 'aluno'
class Aluno(Base):
    __tablename__ = 'aluno'
    id_aluno = Column(Integer, primary_key=True)
    nome = Column(String(255), nullable=False)
    data_nascimento = Column(Date, nullable=True)
    sexo = Column(String(10), nullable=True)
    id_escola = Column(Integer, ForeignKey('escola.id_escola'))
    id_regiao = Column(Integer, ForeignKey('regiao_administrativa.id_regiao'))

    escola = relationship('Escola', backref='alunos')
    regiao = relationship('RegiaoAdministrativa', backref='alunos')

# Definir o modelo da tabela 'exame'
class Exame(Base):
    __tablename__ = 'exame'
    id_exame = Column(Integer, primary_key=True)
    id_aluno = Column(Integer, ForeignKey('aluno.id_aluno'))
    data_exame = Column(Date, nullable=False)
    esferico_od = Column(Float, nullable=True)
    cilindrico_od = Column(Float, nullable=True)
    eixo_od = Column(Integer, nullable=True)
    dioptria_esferica_od = Column(Float, nullable=True)
    esferico_os = Column(Float, nullable=True)
    cilindrico_os = Column(Float, nullable=True)
    eixo_os = Column(Integer, nullable=True)
    dioptria_esferica_os = Column(Float, nullable=True)
    tamanho_pupila_od = Column(Float, nullable=True)
    tamanho_pupila_os = Column(Float, nullable=True)
    observacoes = Column(Text, nullable=True)

    aluno = relationship('Aluno', backref='exames')

# Criar o esquema 'num_piscar_de_olhos' se não existir
with engine.connect() as connection:
    connection.execute(text("CREATE SCHEMA IF NOT EXISTS num_piscar_de_olhos"))
    connection.commit()

# Criar as tabelas no banco (se ainda não existirem)
Base.metadata.create_all(engine)

# Criar uma sessão
session = Session()

# Definir escolas e regiões (para referência)
escolas = [
    Escola(nome="Escola Classe 308 Sul"),
    Escola(nome="Escola Classe 108 Sul"),
    Escola(nome="Colégio Cívico-Militar CED 03 de Sobradinho"),
    Escola(nome="Escola Classe 15 de Planaltina"),
    Escola(nome="Colégio Cívico-Militar CED Estância 3")
]

regioes = [
    RegiaoAdministrativa(nome="Sul", estado="DF"),
    RegiaoAdministrativa(nome="Sobradinho", estado="DF"),
    RegiaoAdministrativa(nome="Planaltina", estado="DF"),
    RegiaoAdministrativa(nome="Estância", estado="DF")
]

# Adicionar as escolas e regiões ao banco
session.add_all(escolas)
session.add_all(regioes)
session.commit()

# Gerar e inserir novos alunos e exames
print("Gerando novos dados...")

for i in range(30000):
    if i % 1000 == 0:  # Mostrar progresso a cada 1000 registros
        print(f"{i} registros inseridos...")

    # Escolher aleatoriamente uma escola e uma região
    escola = random.choice(escolas)
    regiao = random.choice(regioes)

    # Criar novo aluno
    aluno = Aluno(
        nome="Aluno" + str(i),
        data_nascimento=f'{random.randint(2006, 2012)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}',
        sexo=random.choice(["Masculino", "Feminino"]),
        id_escola=escola.id_escola,  # Usar o ID diretamente após o commit
        id_regiao=regiao.id_regiao   # Usar o ID diretamente após o commit
    )
    session.add(aluno)
    session.flush()  # Garante que o id_aluno seja gerado antes de criar o exame

    # Criar novo exame para o aluno
    exame = Exame(
        id_aluno=aluno.id_aluno,
        data_exame=f'2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}',
        esferico_od=random.uniform(-1.0, 2.0),
        cilindrico_od=random.uniform(-1.0, 2.0),
        eixo_od=random.randint(0, 180),
        dioptria_esferica_od=random.uniform(-1.0, 2.0),
        esferico_os=random.uniform(-1.0, 2.0),
        cilindrico_os=random.uniform(-1.0, 2.0),
        eixo_os=random.randint(0, 180),
        dioptria_esferica_os=random.uniform(-1.0, 2.0),
        tamanho_pupila_od=random.uniform(2.0, 6.0),
        tamanho_pupila_os=random.uniform(2.0, 6.0),
        observacoes="Nenhuma"
    )
    session.add(exame)

# Commitar todas as inserções
session.commit()
print("30,000 novos registros inseridos com sucesso!")

# Fechar a sessão
session.close()