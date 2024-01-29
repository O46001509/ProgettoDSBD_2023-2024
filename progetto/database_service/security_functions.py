import os

# Chiave segreta di 32 byte (256 bit)
SECRET_KEY = os.environ.get('SECRET_KEY',111111111)  # Cambia la chiave segreta

# Funzione per cifrare il chat_id
def encrypt_chat_id(chat_id):
    cipher_text = chat_id + int(SECRET_KEY)
    return cipher_text

# Funzione per decifrare il chat_id
def decrypt_chat_id(encrypted_chat_id):
    plain_text = encrypted_chat_id - int(SECRET_KEY)
    return plain_text