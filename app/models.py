from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# --------------------
# MODELS
# --------------------


class Escola(db.Model):
    __tablename__ = 'escola'
    id_escola = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(255), nullable=False)
    logradouro = db.Column(db.String(255), nullable=False)
    numero = db.Column(db.String(10), nullable=False)
    complemento = db.Column(db.String(255))
    bairro = db.Column(db.String(255), nullable=False)
    cidade = db.Column(db.String(255), nullable=False)
    estado = db.Column(db.String(2), nullable=False)
    cep = db.Column(db.String(10), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    regiao_administrativa = db.Column(db.String(30), nullable=False)


class Aluno(db.Model):
    __tablename__ = 'aluno'
    id_aluno = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(255), nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    sexo = db.Column(db.String(10), nullable=False)
    id_escola = db.Column(db.Integer,
                          db.ForeignKey('escola.id_escola'),
                          nullable=False)
    regiao_administrativa = db.Column(db.String(30), nullable=False)

    escola = db.relationship('Escola', backref=db.backref('alunos', lazy=True))


class Exame(db.Model):
    __tablename__ = 'exame'
    id_exame = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_aluno = db.Column(db.Integer,
                         db.ForeignKey('aluno.id_aluno'),
                         nullable=False)

    data_hora_escaneamento = db.Column(db.DateTime, nullable=True)

    raio_corneano_od_mm = db.Column(db.Float, nullable=True)
    eixo_querato_steeper_od = db.Column(db.Float, nullable=True)
    eixo_querato_flatter_od = db.Column(db.Float, nullable=True)

    se_direito = db.Column(db.Float, nullable=True)
    ds_direito = db.Column(db.Float, nullable=True)
    dc_direito = db.Column(db.Float, nullable=True)
    axis_direito = db.Column(db.Integer, nullable=True)

    distancia_interpupilar_mm = db.Column(db.Float, nullable=True)
    input5 = db.Column(db.Float, nullable=True)

    se_esquerdo = db.Column(db.Float, nullable=True)
    ds_esquerdo = db.Column(db.Float, nullable=True)
    dc_esquerdo = db.Column(db.Float, nullable=True)
    axis_esquerdo = db.Column(db.Integer, nullable=True)

    raio_corneano_os_mm = db.Column(db.Float, nullable=True)
    eixo_querato_steeper_os = db.Column(db.Float, nullable=True)
    eixo_querato_flatter_os = db.Column(db.Float, nullable=True)

    aluno = db.relationship('Aluno',
                            backref=db.backref('exames', lazy=True),
                            foreign_keys=[id_aluno])
