from werkzeug.security import generate_password_hash

# --- SCRIPT PARA GERAR HASHES DE SENHA ---

# A nova senha temporária para ambos
new_password = 'Ayanne.Adventure'

# Gera os hashes
hash_gabriel = generate_password_hash(new_password)
hash_ayanne = generate_password_hash(new_password)

print("\n--- HASHES GERADOS COM SUCESSO ---")
print("\nCopie a linha abaixo e cole no SQL Editor para o Gabriel:")
print(f"'{hash_gabriel}'")

print("\nCopie a linha abaixo e cole no SQL Editor para a Ayanne:")
print(f"'{hash_ayanne}'")
print("\n------------------------------------")