import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

# --- SCRIPT PARA RESETAR SENHAS ---
# Este script se conecta ao seu banco de dados e atualiza as senhas.

# --- CONFIGURAÇÃO ---
# Garante que o script encontre o app e os modelos corretamente
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'wayfinders.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELO DE USUÁRIO (copiado do app.py) ---
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

# --- DADOS PARA ATUALIZAR ---
# Defina aqui os usuários e as novas senhas temporárias
users_to_update = {
    'Gabriel': 'wayfinders123',
    'Ayanne': 'wayfinders123'
}

def reset_user_passwords():
    with app.app_context():
        for username, new_password in users_to_update.items():
            user = db.session.query(User).filter_by(username=username).first()
            if user:
                user.password_hash = generate_password_hash(new_password)
                print(f"Senha para o usuário '{username}' foi resetada com sucesso.")
            else:
                print(f"ERRO: Usuário '{username}' não encontrado no banco de dados.")
        db.session.commit()
        print("\nAtualização concluída!")

if __name__ == '__main__':
    reset_user_passwords()