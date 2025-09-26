import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import cloudinary
import cloudinary.uploader
import time
# NOVO: Importa Markup para marcar a string como HTML seguro
from markupsafe import Markup

# --- CONFIGURAÇÃO ---
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

# --- FILTRO NL2BR (VERSÃO SIMPLIFICADA E CORRETA) ---
@app.template_filter()
def nl2br(value):
    if value is None:
        return ''
    # Simplesmente substitui quebras de linha por <br> e retorna como Markup (HTML seguro)
    return Markup(value.replace('\n', '<br>\n'))

# --- MAPEAMENTO DE CARICATURAS ---
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

class MediaItem(db.Model):
    __tablename__ = "media_items"
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(300), nullable=False)
    media_type = db.Column(db.String(10), nullable=False)
    memory_id = db.Column(db.Integer, db.ForeignKey('memories.id'), nullable=False)

class Memory(db.Model):
    __tablename__ = "memories"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, nullable=False, name="event_date")
    description = db.Column(db.Text, nullable=True)
    media_items = db.relationship('MediaItem', backref='memory', lazy=True, cascade="all, delete-orphan")

# --- CALLBACK ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROTAS (sem alterações) ---
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
            return redirect(url_for('loading', username=user.username))
        else:
            flash('Usuário ou senha inválidos. Tente novamente.')
    return render_template('login.html', cache_id=int(time.time()), caricatures=USER_CARICATURES)

@app.route('/loading/<username>')
@login_required
def loading(username):
    caricature_path = USER_CARICATURES.get(username.lower(), '')
    return render_template('loading.html',
                           username=username,
                           caricature_path=caricature_path,
                           cache_id=int(time.time()))

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
    media_files = request.files.getlist('media_files')

    if not title or not event_date_str or not media_files or media_files[0].filename == '':
        flash('Título, data e pelo menos uma mídia são obrigatórios.', 'warning')
        return redirect(url_for('timeline'))

    event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()

    new_memory = Memory(title=title, description=description, date=event_date)
    db.session.add(new_memory)
    db.session.commit()

    for file in media_files:
        if file:
            upload_result = cloudinary.uploader.upload(file, resource_type="auto")
            new_media_item = MediaItem(
                url=upload_result['secure_url'],
                media_type=upload_result['resource_type'],
                memory_id=new_memory.id
            )
            db.session.add(new_media_item)

    db.session.commit()
    flash('Nova memória adicionada com sucesso!', 'success')
    return redirect(url_for('timeline'))

@app.route('/edit-memory/<int:memory_id>', methods=['GET', 'POST'])
@login_required
def edit_memory(memory_id):
    memory = Memory.query.get_or_404(memory_id)
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
    memory = Memory.query.get_or_404(memory_id)
    db.session.delete(memory)
    db.session.commit()
    flash('Memória apagada.', 'info')
    return redirect(url_for('timeline'))

# --- EXECUÇÃO ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)