import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import cloudinary
import cloudinary.uploader
import time

# --- CONFIGURAÇÃO ---
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'uma-chave-padrao-caso-nao-encontre')
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'wayfinders.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

# --- MAPEAMENTO DE CARICATURAS ---
# CORREÇÃO APLICADA AQUI: 'fernanda' foi trocado por 'fê'
USER_CARICATURES = {
    'warny': 'caricaturas/warny.jpg',
    'fê': 'caricaturas/fernanda.jpg',
    'gabriel': 'caricaturas/gabriel.jpg',
    'ayanne': 'caricaturas/ayanne.jpg'
}

# --- MODELOS ---
class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

class Memory(db.Model):
    __tablename__ = "memories"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, nullable=False, name="event_date")
    description = db.Column(db.Text, nullable=True)
    media_url = db.Column(db.String(300), nullable=False)
    media_type = db.Column(db.String(10), nullable=False)

# --- CALLBACK ---
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- ROTAS ---
@app.route('/')
def index():
    return render_template('index.html', cache_id=int(time.time()), caricatures=USER_CARICATURES)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('timeline'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('timeline'))
        else:
            flash('Usuário ou senha inválidos. Tente novamente.')
    return render_template('login.html', cache_id=int(time.time()), caricatures=USER_CARICATURES)

# ... (O resto do seu app.py continua igual, não precisa colar aqui de novo)
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/timeline')
@login_required
def timeline():
    memories = Memory.query.order_by(Memory.date.desc()).all()
    return render_template('timeline.html', memories=memories, cache_id=int(time.time()), caricatures=USER_CARICATURES)

@app.route('/add-memory', methods=['POST'])
@login_required
def add_memory():
    title = request.form.get('title')
    description = request.form.get('description')
    event_date_str = request.form.get('event_date')
    media_file = request.files.get('media_file')
    event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
    upload_result = cloudinary.uploader.upload(media_file, resource_type="auto")
    new_memory = Memory(title=title, description=description, date=event_date, media_url=upload_result['secure_url'], media_type=upload_result['resource_type'])
    db.session.add(new_memory)
    db.session.commit()
    flash('Nova memória adicionada com sucesso!', 'success')
    return redirect(url_for('timeline'))

@app.route('/edit-memory/<int:memory_id>', methods=['GET', 'POST'])
@login_required
def edit_memory(memory_id):
    memory = db.get_or_404(Memory, memory_id)
    if request.method == 'POST':
        memory.title = request.form['title']
        memory.date = datetime.strptime(request.form['event_date'], '%Y-%m-%d').date()
        memory.description = request.form['description']
        db.session.commit()
        flash('Memória atualizada com sucesso!', 'success')
        return redirect(url_for('timeline'))
    return render_template('edit_memory.html', memory=memory, cache_id=int(time.time()), caricatures=USER_CARICATURES)

@app.route('/delete-memory/<int:memory_id>', methods=['POST'])
@login_required
def delete_memory(memory_id):
    memory = db.get_or_404(Memory, memory_id)
    db.session.delete(memory)
    db.session.commit()
    flash('Memória apagada.', 'info')
    return redirect(url_for('timeline'))