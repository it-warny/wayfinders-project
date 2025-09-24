import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

# --- SCRIPT PARA MUDAR A SENHA DE UM USUÁRIO ESPECÍFICO ---

# --- CONFIGURAÇÃO ---
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'wayfinders.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

# --- DADOS PARA ATUALIZAR ---
# Altere o nome do usuário e a nova senha aqui
USERNAME_PARA_MUDAR = 'Ayanne'
NOVA_SENHA_AQUI = 'Ayanne.Adventure' # <-- TROQUE AQUI

def change_user_password():
    with app.app_context():
        user = db.session.query(User).filter_by(username=USERNAME_PARA_MUDAR).first()
        if user:
            user.password_hash = generate_password_hash(NOVA_SENHA_AQUI)
            db.session.commit()
            print(f"\n>>>> Senha para o usuário '{USERNAME_PARA_MUDAR}' foi alterada com sucesso! <<<<")
        else:
            print(f"\nERRO: Usuário '{USERNAME_PARA_MUDAR}' não encontrado.")

if __name__ == '__main__':
    change_user_password()