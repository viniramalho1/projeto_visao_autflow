from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
import subprocess

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/secretaria'
db = SQLAlchemy(app)

class FormEntry(db.Model):
    __tablename__ = 'exames'  # Nome explícito da tabela
    id = db.Column(db.Integer, primary_key=True)
    escola = db.Column(db.String(45), nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False)
    sexo = db.Column(db.String(45), nullable=False)
    nascimento = db.Column(db.Date, nullable=False)
    nome = db.Column(db.String(45), nullable=False)
    sobrenome = db.Column(db.String(45), nullable=False)
    OD1 = db.Column(db.String(45), nullable=False)
    OD2 = db.Column(db.String(45), nullable=False)
    OD3 = db.Column(db.String(45), nullable=False)
    C1 = db.Column(db.String(45), nullable=False)
    C2 = db.Column(db.String(45), nullable=False)
    OE1 = db.Column(db.String(45), nullable=False)
    OE2 = db.Column(db.String(45), nullable=False)
    OE3 = db.Column(db.String(45), nullable=False)
    ODSE = db.Column(db.String(45), nullable=False)
    ODOS = db.Column(db.String(45), nullable=False)
    ODDC = db.Column(db.String(45), nullable=False)
    ODAXIS = db.Column(db.String(45), nullable=False)
    OESE = db.Column(db.String(45), nullable=False)
    OEOS = db.Column(db.String(45), nullable=False)
    OEDC = db.Column(db.String(45), nullable=False)
    OEAXIS = db.Column(db.String(45), nullable=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/formulario', methods=['POST'])
def process_form():
    # Captura os dados do formulário
    escola = request.form.get('InputEscola')
    data_hora = request.form.get('InputDataHoraEscaneamento')
    sexo = request.form.get('InputSexo')
    nascimento = request.form.get('InputNascimento')
    nome = request.form.get('InputNome')
    sobrenome = request.form.get('InputSobrenome')

    # Captura os outros inputs
    OD1 = request.form.get('Input1')
    OD2 = request.form.get('Input2')
    OD3 = request.form.get('Input3')
    C1 = request.form.get('Input4')
    C2 = request.form.get('Input5')
    OE1 = request.form.get('Input6')
    OE2 = request.form.get('Input7')
    OE3 = request.form.get('Input8')
    ODSE = request.form.get('Input9')
    ODOS = request.form.get('Input10')
    ODDC = request.form.get('Input11')
    ODAXIS = request.form.get('Input12')
    OESE = request.form.get('Input13')
    OEOS = request.form.get('Input14')
    OEDC = request.form.get('Input15')
    OEAXIS = request.form.get('Input16')

    # Processa os dados como necessário
    novo_dado = FormEntry(
        escola=escola, data_hora=data_hora, sexo=sexo, nascimento=nascimento, 
        nome=nome, sobrenome=sobrenome, OD1=OD1, OD2=OD2, OD3=OD3, C1=C1, 
        C2=C2, OE1=OE1, OE2=OE2, OE3=OE3, ODSE=ODSE, ODOS=ODOS, ODDC=ODDC, 
        ODAXIS=ODAXIS, OESE=OESE, OEOS=OEOS, OEDC=OEDC, OEAXIS=OEAXIS
    )

    # Adiciona e comita a nova entrada ao banco de dados
    db.session.add(novo_dado)
    db.session.commit()

    # Para este exemplo, redirecionamos para a página inicial
    return redirect(url_for('index'))

# Subprocesso para iniciar o Streamlit
def start_streamlit():
    subprocess.Popen(["streamlit", "run", "./dash/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"])

# Inicia o Streamlit quando o Flask é carregado
with app.app_context():
    start_streamlit()

# Rota para fornecer dados
@app.route('/api/data', methods=['GET'])
def streamlit_dashboard():
    # Redireciona diretamente para o Streamlit
    return redirect("http://localhost:8501", code=302)

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=5000)
