from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
plaintext_password = "admin123"
hashed_password = bcrypt.generate_password_hash(plaintext_password).decode('utf-8')

print("Hashed Password:", hashed_password)
