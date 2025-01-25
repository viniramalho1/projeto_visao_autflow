from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base  # Importe declarative_base diretamente
import random

# Define a string de conexão para o seu banco de dados
connection_string = 'postgresql+psycopg2://admin:WUvU8D5EFk5WLn0fOjtByT5pF91SzCsX@dpg-cpkt62q0si5c73d1kmf0-a.oregon-postgres.render.com/oftalmologista'

# Crie um engine
engine = create_engine(connection_string)

# Crie um session maker
Session = sessionmaker(bind=engine)

# Crie uma classe base para seus modelos
Base = declarative_base()  # Ajuste a importação

# Defina o seu modelo
class FormEntry(Base):
    __tablename__ = 'exames'  # Nome explícito da tabela
    id = Column(Integer, primary_key=True)
    escola = Column(String(45), nullable=False)
    data_hora = Column(DateTime, nullable=False)
    sexo = Column(String(45), nullable=False)
    nascimento = Column(Date, nullable=False)
    nome = Column(String(45), nullable=False)
    sobrenome = Column(String(45), nullable=False)
    OD1 = Column(String(45), nullable=False)
    OD2 = Column(String(45), nullable=False)
    OD3 = Column(String(45), nullable=False)
    C1 = Column(String(45), nullable=False)
    C2 = Column(String(45), nullable=False)
    OE1 = Column(String(45), nullable=False)
    OE2 = Column(String(45), nullable=False)
    OE3 = Column(String(45), nullable=False)
    ODSE = Column(String(45), nullable=False)
    ODOS = Column(String(45), nullable=False)
    ODDC = Column(String(45), nullable=False)
    ODAXIS = Column(String(45), nullable=False)
    OESE = Column(String(45), nullable=False)
    OEOS = Column(String(45), nullable=False)
    OEDC = Column(String(45), nullable=False)
    OEAXIS = Column(String(45), nullable=False)

# Crie as tabelas no banco de dados
Base.metadata.create_all(engine)

# Crie uma sessão
session = Session()

a = 0
# Gere e insira dados no banco de dados
for i in range(30000):
    a += 1
    print(a)
    genero = ["Masculino", "Feminino"]
    escola = ["Escola Classe 308 Sul", "Escola Classe 108 Sul", "Colégio Cívico-Militar CED 03 de Sobradinho", "Colégio Cívico-Militar CED Estância 3", "Escola Classe 15 de Planaltina"]
    axis1 = random.randint(0, 180)
    axis2 = random.randint(0, 180)

    # Processar dados conforme necessário
    novo_dado = FormEntry(
        escola=random.choice(escola), data_hora='2024-' + f'{random.randint(1, 12):02}' + '-' + f'{random.randint(1, 28):02}' + 'T19:30', sexo=random.choice(genero), nascimento=f'{random.randint(2006, 2012)}-' + f'{random.randint(1, 12):02}-' + f'{random.randint(1, 28):02}', 
        nome="nome", sobrenome="sobrenome", OD1=str(round(random.uniform(-1.0, 2.0), 2)), OD2=str(round(random.uniform(-1.0, 2.0), 2)), OD3=str(round(random.uniform(-1.0, 2.0), 2)), C1=str(round(random.uniform(-1.0, 2.0), 2)), 
        C2=str(round(random.uniform(-1.0, 2.0), 2)), OE1=str(round(random.uniform(-1.0, 2.0), 2)), OE2=str(round(random.uniform(-1.0, 2.0), 2)), OE3=str(round(random.uniform(-1.0, 2.0), 2)), ODSE=str(round(random.uniform(-1.0, 2.0), 2)), ODOS=str(round(random.uniform(-1.0, 2.0), 2)), ODDC=str(round(random.uniform(-1.0, 2.0), 2)), 
        ODAXIS='@' + str(axis1) + 'º', OESE=str(round(random.uniform(-1.0, 2.0), 2)), OEOS=str(round(random.uniform(-1.0, 2.0), 2)), OEDC=str(round(random.uniform(-1.0, 2.0), 2)), OEAXIS='@' + str(axis2) + 'º'
    )

    # Adicionar e comitar a nova entrada no banco de dados
    session.add(novo_dado)
    session.commit()

# Fechar a sessão
session.close()
