import os

SECRET_KEY = os.environ.get('SECRET_KEY',111111111)  
# Da cambiare la chiave segreta o il meccanismo di sicurezza per un'implementazione più robusta.

# Funzione per cifrare il chat_id
def encrypt_chat_id(chat_id):
    cipher_text = chat_id + int(SECRET_KEY)
    return cipher_text

# Funzione per decifrare il chat_id
def decrypt_chat_id(encrypted_chat_id):
    plain_text = encrypted_chat_id - int(SECRET_KEY)
    return plain_text