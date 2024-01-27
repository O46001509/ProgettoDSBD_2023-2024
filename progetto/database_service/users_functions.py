from flask import request, jsonify
from security_functions import encrypt_chat_id, decrypt_chat_id
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def aggiungi_utente(conn, cur):
    try:
        data = request.get_json()
        user_name = data.get('user_name')
        chat_id = data.get('chat_id')
        interval = data.get('interval')
        encrypted_chat_id = encrypt_chat_id(int(chat_id))

        logging.info(f"Inserimento utente - User name: {user_name}, chat_id: *********, interval: {interval}")

        cur.execute("INSERT INTO users (user_name, chat_id, interval) VALUES (%s, %s, %s)", (user_name, encrypted_chat_id, interval))
        conn.commit()

        return jsonify({'message': 'Utente aggiunto con successo!'}), 201
    except Exception as e:
        conn.rollback()  # Annulla la transazione in caso di errore
        logging.error(f"Errore durante l'inserimento dell'utente: {e}")
        return jsonify({'error': f"Errore durante l'inserimento dell'utente: {e}"}), 500
    
def recupera_utente(cur):
    try:
        user_name = request.args.get('user_name')
        chat_id = request.args.get('chat_id')
        encrypted_chat_id = encrypt_chat_id(int(chat_id))

        if user_name and chat_id:
            # Recupera l'utente sia con user_name che con chat_id
            cur.execute("SELECT user_name, chat_id, interval FROM users WHERE user_name = %s AND chat_id = %s", (user_name, encrypted_chat_id))
            user = cur.fetchone()
            if user:
                decrypted_chat_id = decrypt_chat_id(user[1])  # user[1] è l'indice del chat_id criptato
                logging.info(f"Recupero utente - User name: {user_name}, chat_id: *********")
                return jsonify({'user_name': user[0], 'decrypted_chat_id': decrypted_chat_id, 'interval': user[2]}), 200
            else:
                # Se non trovato con user_name e chat_id, tenta di trovare solo con chat_id
                cur.execute("SELECT user_name, chat_id, interval FROM users WHERE chat_id = %s", (encrypted_chat_id,))
                user = cur.fetchone()
                if user:
                    decrypted_chat_id = decrypt_chat_id(user[1])
                    logging.info(f"Recupero utente - chat_id: *********")
                    return jsonify({'user_name': user[0], 'decrypted_chat_id': decrypted_chat_id, 'interval': user[2]}), 201
                else:
                    return jsonify({'error': 'Utente non trovato con lo stesso chat_id'}), 404
        else:
            return jsonify({'error': 'Parametri mancanti'}), 400
    except Exception as e:
        logging.error(f"Errore durante il recupero dell'utente: {e}")
        return jsonify({'error': f"Errore durante il recupero dell'utente: {e}"}), 500
    
def recupero_intervallo(cur):
    try:
        chat_id = request.args.get('chat_id')
        encrypted_chat_id = encrypt_chat_id(int(chat_id))
        if chat_id:
            # Recupera l'utente sia con user_name che con chat_id
            cur.execute("SELECT interval FROM users WHERE chat_id = %s", (encrypted_chat_id,))
            user = cur.fetchone()
            if user:
                logging.info(f"Recupero intervallo - chat_id: *********")
                return jsonify({'interval': user[0]}), 200
            else:
                return jsonify({'error': 'Utente non trovato con lo stesso chat_id'}), 404
        else:
            return jsonify({'error': 'Parametri mancanti'}), 400
    except Exception as e:
        logging.error(f"Errore durante il recupero dell'intervallo: {e}")
        return jsonify({'error': f"Errore durante il recupero dell'intervallo: {e}"}), 500
    
def verifica_utente_(cur):
    try:
        user_name = request.args.get('user_name')

        if not user_name:
            return jsonify({'error': 'Specificare user_name come parametro nella richiesta'}), 400
        
        logging.info(f"Verifica utente - user_name: {user_name}")

        cur.execute("SELECT * FROM users WHERE user_name = %s", (user_name,))
        user = cur.fetchone()

        if user:
            # Se l'utente esiste nel database con lo stesso user_name
            return jsonify({'message': 'L\'utente esiste'}), 200
        else:
            # Se non esiste un utente con quel user_name
            return jsonify({'error': 'L\'utente non esiste'}), 404

    except Exception as e:
        logging.error(f"Errore durante la verifica dell'utente: {e}")
        return jsonify({'error': f"Errore durante la verifica dell'utente: {e}"}), 500
    
def aggiorna_utente(conn, cur):
    try:
        data = request.get_json()
        chat_id = data.get('chat_id')
        new_user_name = data.get('new_user_name')
        encrypted_chat_id = encrypt_chat_id(int(chat_id))

        logging.info(f"Aggiornamento - new user name: {new_user_name}, chat_id: ********")

        cur.execute("UPDATE users SET user_name = %s WHERE chat_id = %s", (new_user_name, encrypted_chat_id))
        conn.commit()
        return jsonify({'message': 'Nome utente aggiornato con successo!'}), 200
    except Exception as e:
        conn.rollback()  # Annulla la transazione in caso di errore
        logging.error(f"Errore durante l'aggiornamento dell'utente: {e}")
        return jsonify({'error': f"Errore durante l'aggiornamento del nome utente: {e}"}), 500
    
def aggiorna_intervallo(conn, cur):
    try:
        data = request.get_json()
        chat_id = data.get('chat_id')
        user_name = data.get('user_name')
        interval = data.get('interval')
        encrypted_chat_id = encrypt_chat_id(int(chat_id))

        logging.info(f"Aggiornamento intervallo - user name: {user_name}, new interval: {interval}")

        cur.execute("UPDATE users SET interval = %s WHERE chat_id = %s", (interval, encrypted_chat_id))
        conn.commit()

        return jsonify({'message': 'Intervallo aggiornato con successo!'}), 200
    except Exception as e:
        conn.rollback()  # Annulla la transazione in caso di errore
        logging.error(f"Errore durante l'aggiornamento dell'intervallo: {e}")
        return jsonify({'error': f"Errore durante l'aggiornamento dell'intervallo: {e}"}), 500
    
def get_user_names(cur):
    try:
        cur.execute("SELECT user_name FROM users")
        user_names = cur.fetchall()
        user_names_list = [user[0] for user in user_names]
        return jsonify(user_names_list), 200
    except Exception as e:
        return jsonify({'error': f"Errore durante la richiesta degli user_name: {e}"}), 500
    
def get_chat_id(cur):
    try:
        user_name = request.args.get('user_name')

        if not user_name:
            return jsonify({'error': 'Specificare user_name come parametro nella richiesta'}), 400

        cur.execute("SELECT chat_id FROM users WHERE user_name = %s", (user_name,))
        result = cur.fetchone()

        if result:
            decrypted_chat_id = decrypt_chat_id(result[0])
            logging.info(f"chat_id recuperato")
            return jsonify({'user_name': user_name, 'decrypted_chat_id': decrypted_chat_id}), 200
        else:
            return jsonify({'message': 'Utente non trovato con lo stesso user_name'}), 404

    except Exception as e:
        return jsonify({'error': f"Errore durante la richiesta del chat_id: {e}"}), 500