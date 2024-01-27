from flask import request, jsonify
import json, logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def request_get_sottoscrizioni(cur):
    try:
        user_name = request.args.get('user_name')

        if not user_name:
            return jsonify({'error': 'Specificare user_name come parametro nella richiesta'}), 400

        cur.execute("SELECT * FROM subscriptions WHERE user_name = %s", (user_name,))
        subscriptions = cur.fetchall()
        subscriptions_list = []
        for sub in subscriptions:
            subscriptions_list.append({
                'user_id': sub[1],
                'citta': sub[2],
                'condizioni': sub[3]
            })
        return jsonify(subscriptions_list), 200
    except Exception as e:
        logging.error(f"Errore durante la richiesta delle sottoscrizioni: {e}")
        return jsonify({'error': f"Errore durante la richiesta delle sottoscrizioni: {e}"}), 500
    
def request_post_sottoscrizioni(conn, cur):
    try:
        data = request.get_json()
        user_name = data.get('user_name')
        citta = data.get('citta') 
        condizioni = data.get('condizioni')
        condizioni_json = json.dumps(condizioni)
        logging.info(f"Inserimento sottoscrizione - User name: {user_name}, chat_id: {citta}, conditions: {condizioni}")

        cur.execute("INSERT INTO subscriptions (user_name, citta, condizioni) VALUES (%s, %s, %s)",
                    (user_name, citta, condizioni_json))
        conn.commit()

        return jsonify({'message': 'Sottoscrizione creata con successo!'}), 201
    except Exception as e:
        conn.rollback()  # Annulla la transazione in caso di errore
        logging.error(f"Errore durante l'inserimento della sottoscrizione: {e}")
        return jsonify({'error': f"Errore durante l'inserimento della sottoscrizione: {e}"}), 500

def request_put_sottoscrizioni(conn, cur):
    try:
        data = request.get_json()
        user_name = data.get('user_name')
        citta = data.get('citta')
        nuove_condizioni = data.get('nuove_condizioni')
        
        if not user_name or not citta:
            return jsonify({'error': 'Specificare user_name e citta come parametri nella richiesta'}), 400
        
        logging.info(f"Aggiornamento sottoscrizione - User name: {user_name}, chat_id: {citta}")

        # Verifico l'esistenza della sottoscrizione
        cur.execute("SELECT * FROM subscriptions WHERE user_name = %s AND citta = %s", (user_name, citta))
        subscription = cur.fetchone()

        if not subscription:
            return jsonify({'error': 'Sottoscrizione non trovata'}), 404
        
        # Aggiorno la sottoscrizione con le nuove condizioni
        cur.execute("UPDATE subscriptions SET condizioni = %s WHERE user_name = %s AND citta = %s",
                    (json.dumps(nuove_condizioni), user_name, citta))
        conn.commit()

        return jsonify({'message': 'Sottoscrizione aggiornata con successo!'}), 200

    except Exception as e:
        conn.rollback()  # Annulla la transazione in caso di errore
        logging.error(f"Errore durante l'aggiornamento della sottoscrizione: {e}")
        return jsonify({'error': f"Errore durante l'aggiornamento della sottoscrizione: {e}"}), 500
    
def verifica_sottoscrizione(cur):
    try:
        data = request.get_json()
        user_name = data.get('user_name')
        city = data.get('citta')

        if not user_name or not city:
            return jsonify({'error': 'Specificare user_name e citta come parametri nella richiesta'}), 400

        cur.execute("SELECT * FROM subscriptions WHERE user_name = %s AND citta = %s", (user_name, city))
        subscription = cur.fetchone()

        if subscription:
            return jsonify({'message': 'La sottoscrizione esiste'}), 200
        else:
            return jsonify({'error': 'La sottoscrizione non esiste'}), 404

    except Exception as e:
        return jsonify({'error': f"Errore durante la verifica della sottoscrizione: {e}"}), 500
    
def cancella_sottoscrizione(conn, cur):
    try:
        data = request.get_json()
        user_name = data.get('user_name')
        citta = data.get('citta')

        if not user_name or not citta:
            return jsonify({'error': 'Specificare user_name e citta come parametri nella richiesta'}), 400
        
        logging.info(f"Cancellazione sottoscrizione - User name: {user_name}, chat_id: {citta}")
        cur.execute("DELETE FROM subscriptions WHERE user_name = %s AND citta = %s", (user_name, citta))
        conn.commit()

        return jsonify({'message': 'Sottoscrizione cancellata con successo!'}), 200

    except Exception as e:
        return jsonify({'error': f"Errore durante la cancellazione della sottoscrizione: {e}"}), 500