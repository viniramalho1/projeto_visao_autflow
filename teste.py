import random
from faker import Faker
import psycopg2
from psycopg2 import sql

# Configurações de conexão com o banco de dados
def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="postgres",
        user="meu_usuario",
        password="minha_senha"
    )

# Gera dados falsos
fake = Faker()

def insert_regioes_administrativas(cursor, qtd=5):
    for _ in range(qtd):
        cursor.execute(
            "INSERT INTO postgres.num_piscar_de_olhos.regiao_administrativa (Nome, Estado) VALUES (%s, %s)",
            (fake.city(), fake.state_abbr())
        )

def insert_enderecos(cursor, qtd=10):
    cursor.execute("SELECT ID_Regiao FROM postgres.num_piscar_de_olhos.regiao_administrativa")
    regioes = [row[0] for row in cursor.fetchall()]

    for _ in range(qtd):
        cursor.execute(
            """INSERT INTO postgres.num_piscar_de_olhos.endereco
            (Logradouro, Numero, Complemento, Bairro, Cidade, Estado, CEP, Latitude, Longitude, ID_Regiao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                fake.street_name(),
                fake.building_number(),
                fake.secondary_address(),
                fake.city_suffix(),
                fake.city(),
                fake.state_abbr(),
                fake.zipcode(),
                fake.latitude(),
                fake.longitude(),
                random.choice(regioes) if regioes else None
            )
        )

def insert_escolas(cursor, qtd=5):
    cursor.execute("SELECT ID_Endereco FROM postgres.num_piscar_de_olhos.endereco")
    enderecos = [row[0] for row in cursor.fetchall()]

    for _ in range(qtd):
        cursor.execute(
            "INSERT INTO postgres.num_piscar_de_olhos.escola (Nome, ID_Endereco) VALUES (%s, %s)",
            (
                fake.company(),
                random.choice(enderecos) if enderecos else None
            )
        )

def insert_alunos(cursor, qtd=20):
    cursor.execute("SELECT ID_Escola FROM postgres.num_piscar_de_olhos.escola")
    escolas = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT ID_Regiao FROM postgres.num_piscar_de_olhos.regiao_administrativa")
    regioes = [row[0] for row in cursor.fetchall()]

    for _ in range(qtd):
        cursor.execute(
            """INSERT INTO postgres.num_piscar_de_olhos.aluno (Nome, Data_Nascimento, Sexo, ID_Escola, ID_Regiao)
            VALUES (%s, %s, %s, %s, %s)""",
            (
                fake.name(),
                fake.date_of_birth(minimum_age=5, maximum_age=18),
                random.choice(["Masculino", "Feminino"]),
                random.choice(escolas) if escolas else None,
                random.choice(regioes) if regioes else None
            )
        )

def insert_exames(cursor, qtd=50):
    cursor.execute("SELECT ID_Aluno FROM postgres.num_piscar_de_olhos.aluno")
    alunos = [row[0] for row in cursor.fetchall()]

    for _ in range(qtd):
        cursor.execute(
            """INSERT INTO postgres.num_piscar_de_olhos.exame
            (ID_Aluno, Data_Exame, Esferico_OD, Cilindrico_OD, Eixo_OD, Dioptria_Esferica_OD, 
             Esferico_OS, Cilindrico_OS, Eixo_OS, Dioptria_Esferica_OS, 
             Tamanho_Pupila_OD, Tamanho_Pupila_OS, Observacoes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                random.choice(alunos) if alunos else None,
                fake.date_this_year(),
                round(random.uniform(-6.0, 6.0), 2),
                round(random.uniform(-2.0, 2.0), 2),
                random.randint(0, 180),
                round(random.uniform(-6.0, 6.0), 2),
                round(random.uniform(-6.0, 6.0), 2),
                round(random.uniform(-2.0, 2.0), 2),
                random.randint(0, 180),
                round(random.uniform(-6.0, 6.0), 2),
                round(random.uniform(2.0, 8.0), 1),
                round(random.uniform(2.0, 8.0), 1),
                fake.text(max_nb_chars=100)
            )
        )

def main():
    for i in range(100):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            insert_regioes_administrativas(cursor)
            insert_enderecos(cursor)
            insert_escolas(cursor)
            insert_alunos(cursor)
            insert_exames(cursor)
            conn.commit()
            print("Dados inseridos com sucesso!")
        except Exception as e:
            conn.rollback()
            print("Erro ao inserir dados:", e)
        finally:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    main()
