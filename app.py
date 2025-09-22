import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
# Importamos a biblioteca do Cloudinary
import cloudinary
import cloudinary.uploader

# --- CONFIGURAÇÃO INICIAL E SEGURA ---
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
# Agora a SECRET_KEY vem de uma variável de ambiente
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'uma-chave-padrao-caso-nao-encontre')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'wayfinders.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- CONFIGURAÇÃO DO CLOUDINARY (LENDO VARIÁVEIS DE AMBIENTE) ---
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

# --- MODELOS DO BANCO DE DADOS (sem mudanças) ---
class User(db.Model, UserMixin):
    # ... (código igual ao anterior)
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

class Memory(db.Model):
    # ... (código igual ao anterior)
    __tablename__ = "memories"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=True)
    media_url = db.Column(db.String(300), nullable=False)
    media_type = db.Column(db.String(10), nullable=False)


# --- FUNÇÃO DE CALLBACK DO FLASK-LOGIN (sem mudanças) ---
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# --- ROTAS ---
# ... (rotas de index, login, logout sem mudanças)
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('timeline'))
        else:
            flash('Usuário ou senha inválidos. Tente novamente.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/timeline')
@login_required
def timeline():
    memories = Memory.query.order_by(Memory.event_date.desc()).all()
    return render_template('timeline.html', memories=memories)

# ROTA add_memory TOTALMENTE ATUALIZADA
@app.route('/add-memory', methods=['POST'])
@login_required
def add_memory():
    title = request.form['title']
    event_date_str = request.form['event_date']
    description = request.form['description']
    # Agora pegamos o arquivo enviado pelo formulário
    media_file = request.files.get('media_file')

    # Validação básica
    if not all([title, event_date_str, media_file]):
        flash('Título, data e arquivo de mídia são obrigatórios!')
        return redirect(url_for('timeline'))

    # Faz o upload do arquivo para o Cloudinary
    upload_result = cloudinary.uploader.upload(media_file)
    # A URL segura do arquivo na nuvem
    media_url = upload_result['secure_url']

    event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
    # O Cloudinary já nos diz se o arquivo é imagem ou vídeo!
    media_type = upload_result['resource_type']

    new_memory = Memory(
        title=title, event_date=event_date, description=description,
        media_url=media_url, media_type=media_type
    )

    db.session.add(new_memory)
    db.session.commit()

    return redirect(url_for('timeline'))


# --- EXECUÇÃO ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)