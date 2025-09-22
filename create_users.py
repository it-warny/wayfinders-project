# Este script serve apenas para criar os usuários iniciais no banco de dados.
# Ele só precisa ser executado uma única vez.

from app import app, db, User
# Importamos a ferramenta para gerar o hash da senha
from werkzeug.security import generate_password_hash

# Lista dos 4 usuários que terão acesso
users_to_create = [
    {'username': 'Warny', 'password': 'Warny.Way'},
    {'username': 'Fê', 'password': 'Fê.Finders'},
    {'username': 'Gabriel', 'password': 'Biel.Great'},
    {'username': 'Ayanne', 'password': 'Ayanne.Adventures'}
]

# O 'with app.app_context()' garante que a aplicação Flask está 'ativa'
# para que possamos interagir com o banco de dados.
with app.app_context():
    print("Criando usuários...")
    for user_data in users_to_create:
        # Verifica se o usuário já não existe
        existing_user = User.query.filter_by(username=user_data['username']).first()
        if not existing_user:
            # Gera o hash seguro da senha
            hashed_password = generate_password_hash(user_data['password'], method='pbkdf2:sha256')
            # Cria o novo objeto User
            new_user = User(username=user_data['username'], password_hash=hashed_password)
            # Adiciona ao banco de dados
            db.session.add(new_user)
            print(f"Usuário '{user_data['username']}' criado.")
        else:
            print(f"Usuário '{user_data['username']}' já existe.")

    # Salva todas as alterações no banco
    db.session.commit()
    print("Processo finalizado.")