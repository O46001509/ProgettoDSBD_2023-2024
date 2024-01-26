from flask import Flask, jsonify, request, Response
import psycopg2, time, os, json
import logging
from prometheus_flask_exporter import PrometheusMetrics


logging.basicConfig(level=logging.INFO)  # Imposta il livello di logging a INFO

time.sleep(3)

app = Flask(__name__)

# Configura le metriche Prometheus
metrics = PrometheusMetrics(app)

# Definisci le tue metriche personalizzate qui

# Endpoint /metrics per esporre le metriche a Prometheus
@app.route('/metrics')
def metrics():
    from prometheus_client import generate_latest
    return Response(generate_latest(), mimetype='text/plain')

# Chiave segreta di 32 byte (256 bit)
SECRET_KEY = 111111111  # Cambia la chiave segreta

host = os.environ.get('POSTGRES_HOST','NO VARIABLE POSTGRES_HOST'),
user = os.environ.get('POSTGRES_USER','NO VARIABLE POSTGRES_USER'),
password = os.environ.get('POSTGRES_PASSWORD','NO VARIABLE POSTGRES_PASSWORD'),
database = os.environ.get('POSTGRES_DATABASE','NO VARIABLE POSTGRES_DATABASE')

#connessione al db
conn = psycopg2.connect(    
        host = host[0],
        port = 5432,
        user = user[0],
        password = password[0],
        database = database)
cur = conn.cursor()

# Funzione per cifrare il chat_id
def encrypt_chat_id(chat_id):
    cipher_text = chat_id + SECRET_KEY
    return cipher_text

# Funzione per decifrare il chat_id
def decrypt_chat_id(encrypted_chat_id):
    plain_text = encrypted_chat_id - SECRET_KEY
    return plain_text

@app.route('/crea_tabella_utenti', methods=['POST'])
def create_users():
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                user_name VARCHAR(255),
                chat_id INTEGER 
            );
        """)
        conn.commit()
        return jsonify({'message': 'Tabella degli utenti creata con successo!'}), 201
    except Exception as e:
        return jsonify({'error': f"Errore durante la creazione della tabella users: {e}"}), 500

@app.route('/crea_tabella_sottoscrizioni', methods=['POST'])
def create_subscriptions_table():
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions(
                id SERIAL PRIMARY KEY,
                user_name VARCHAR(50) NOT NULL,
                citta VARCHAR(50) NOT NULL,
                condizioni JSON NOT NULL
            );
        """)
        conn.commit()
        return jsonify({'message': 'Tabella delle sottoscrizioni creata con successo!'}), 201
    except Exception as e:
        return jsonify({'error': f"Errore durante la creazione della tabella subscriptions: {e}"}), 500
    
@app.route('/crea_tabella_sla_definitions', methods=['POST'])
def create_sla_definitions_table():
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sla_definitions (
                sla_id SERIAL PRIMARY KEY,
                metric_name VARCHAR(255) NOT NULL,
                threshold DECIMAL NOT NULL,
                description TEXT
            );
        """ )
        conn.commit()
        return jsonify({'message': 'Tabella del sla_definitos creata con successo!'}), 201
    except Exception as e:
        return jsonify({'error': f"Errore durante la creazione della tabella sla_definitions: {e}" }), 500

@app.route('/crea_tabella_sla_violations', methods=['POST'])
def create_sla_violations_table():
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sla_violations ( 
                violation_id SERIAL PRIMARY KEY,
                sla_id INT NOT NULL,
                violation_time TIMESTAMP NOT NULL,
                actual_value DECIMAL NOT NULL,
                FOREIGN KEY (sla_id) REFERENCES sla_definitions(sla_id)
            );
        """)
        conn.commit()
        return jsonify({'message': 'Tabella sla_violations creata con successo!'}), 201
    except Exception as e:
        return jsonify({'error': f"Errore durante la creazione della tabella sla_violations: {e}"}), 500


@app.route('/sottoscrizioni', methods=['GET','POST'])
def manage_subscriptions():
    if request.method == 'GET':
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
            return jsonify({'error': f"Errore durante la richiesta delle sottoscrizioni: {e}"}), 500
    elif request.method == 'POST':
        data = request.get_json()
        user_name = data.get('user_name')
        citta = data.get('citta') 
        condizioni = data.get('condizioni')
        condizioni_json = json.dumps(condizioni)

        cur.execute("INSERT INTO subscriptions (user_name, citta, condizioni) VALUES (%s, %s, %s)",
                    (user_name, citta, condizioni_json))
        conn.commit()

        return jsonify({'message': 'Sottoscrizione creata con successo!'}), 201

@app.route('/notifiche', methods=['POST'])
def receive_notification():
    data = request.get_json()
    user_name = data.get('user_name')
    message = data.get('message')

    cur.execute("SELECT * FROM subscriptions WHERE user_name = %s", (user_name,))
    subscription = cur.fetchone()
    if subscription:
        # Invio notifica all'utente usando le informazioni della sottoscrizione
        # ... ancora da gestire e vedere se usare
        print(subscription)

    return jsonify({'message': 'Notifica inviata con successo!'}), 200

@app.route('/aggiungi_utente', methods=['POST'])
def add_user():
    data = request.get_json()
    user_name = data.get('user_name')
    chat_id = data.get('chat_id')

    encrypted_chat_id = encrypt_chat_id(int(chat_id))
    cur.execute("INSERT INTO users (user_name, chat_id) VALUES (%s, %s)", (user_name, encrypted_chat_id))
    conn.commit()

    return jsonify({'message': 'Utente aggiunto con successo!'}), 201

@app.route('/recupera_utente', methods=['GET'])
def get_user():
    user_name = request.args.get('user_name')
    chat_id = request.args.get('chat_id')
    logging.info(f"User name: {user_name}, chat_id: {chat_id}")
    encrypted_chat_id = encrypt_chat_id(int(chat_id))
    if user_name and chat_id:
        # Recupera l'utente sia con user_name che con chat_id
        cur.execute("SELECT * FROM users WHERE user_name = %s AND chat_id = %s", (user_name, encrypted_chat_id))
        user = cur.fetchone()
        if user:
            decrypted_chat_id = decrypt_chat_id(user[2])
            return jsonify({'user_name': user[1], 'decrypted_chat_id': decrypted_chat_id}), 200
        else:
            #return jsonify({'message': 'Utente non trovato con lo stesso chat_id e nome_utente'}), 404
            if chat_id:
                # Recupera l'utente solo con chat_id
                logging.info(f"if chat_id: {chat_id}")

                cur.execute("SELECT * FROM users WHERE chat_id = %s", (encrypted_chat_id,))
                user = cur.fetchone()
                if user:
                    
                    decrypted_chat_id = decrypt_chat_id(user[2])
                    return jsonify({'user_name': user[1], 'decrypted_chat_id': decrypted_chat_id}), 201
                else:
                    return jsonify({'message': 'Utente non trovato con lo stesso chat_id'}), 404
    else:
        return jsonify({'message': 'Parametri mancanti'}), 400

@app.route('/aggiorna_utente', methods=['PUT'])
def update_user():
    data = request.get_json()
    chat_id = data.get('chat_id')
    new_user_name = data.get('new_user_name')
    logging.info(f"new user name: {new_user_name}, chat_id {chat_id}")
    encrypted_chat_id = encrypt_chat_id(int(chat_id))

    try:
        cur.execute("UPDATE users SET user_name = %s WHERE chat_id = %s", (new_user_name, encrypted_chat_id))
        conn.commit()
        return jsonify({'message': 'Nome utente aggiornato con successo!'}), 200
    except Exception as e:
        return jsonify({'error': f"Errore durante l'aggiornamento del nome utente: {e}"}), 500
    
@app.route('/utenti_user_name', methods=['GET'])
def get_all_user_names():
    try:
        cur.execute("SELECT user_name FROM users")
        user_names = cur.fetchall()
        user_names_list = [user[0] for user in user_names]
        return jsonify(user_names_list), 200
    except Exception as e:
        return jsonify({'error': f"Errore durante la richiesta degli user_name: {e}"}), 500
    
@app.route('/utenti', methods=['GET'])
def get_subscriptions_by_user_name():
    try:
        user_name = request.args.get('user_name')

        if not user_name:
            return jsonify({'error': 'Specificare user_name come parametro nella richiesta'}), 400

        cur.execute("SELECT * FROM subscription WHERE user_name = %s", (user_name,))
        subscriptions = cur.fetchall()
        subscriptions_list = []

        for subscription in subscriptions:
            subscriptions_list.append({
                'subscription_id': subscription[0],
                'chat_id': subscription[1],
                'user_name': subscription[2],
                # Altre colonne che desideri includere
            })

        return jsonify(subscriptions_list), 200
    except Exception as e:
        return jsonify({'error': f"Errore durante la richiesta delle sottoscrizioni: {e}"}), 500
    
@app.route('/chat_id', methods=['GET'])
def get_chat_id_by_user_name():
    try:
        user_name = request.args.get('user_name')

        if not user_name:
            return jsonify({'error': 'Specificare user_name come parametro nella richiesta'}), 400

        cur.execute("SELECT chat_id FROM users WHERE user_name = %s", (user_name,))
        result = cur.fetchone()

        if result:
            decrypted_chat_id = decrypt_chat_id(result[0])
            logging.info(f"chat_id recuperato{decrypted_chat_id} + result {result}")
            return jsonify({'user_name': user_name, 'decrypted_chat_id': decrypted_chat_id}), 200
        else:
            return jsonify({'message': 'Utente non trovato con lo stesso user_name'}), 404

    except Exception as e:
        return jsonify({'error': f"Errore durante la richiesta del chat_id: {e}"}), 500
    
# Endpoint per verificare l'esistenza di una sottoscrizione
@app.route('/verifica_sottoscrizione', methods=['POST'])
def verify_subscription():
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

# Endpoint per cancellare una sottoscrizione
@app.route('/cancella_sottoscrizione', methods=['POST'])
def delete_subscription():
    try:
        data = request.get_json()
        user_name = data.get('user_name')
        city = data.get('citta')

        if not user_name or not city:
            return jsonify({'error': 'Specificare user_name e citta come parametri nella richiesta'}), 400

        cur.execute("DELETE FROM subscriptions WHERE user_name = %s AND citta = %s", (user_name, city))
        conn.commit()

        return jsonify({'message': 'Sottoscrizione cancellata con successo!'}), 200

    except Exception as e:
        return jsonify({'error': f"Errore durante la cancellazione della sottoscrizione: {e}"}), 500
    
@app.route('/aggiorna_sottoscrizione', methods=['PUT'])
def update_subscription():
    data = request.get_json()
    user_name = data.get('user_name')
    citta = data.get('citta')
    nuove_condizioni = data.get('nuove_condizioni')

    if not user_name or not citta:
        return jsonify({'error': 'Specificare user_name e citta come parametri nella richiesta'}), 400

    try:
        # Verifica l'esistenza della sottoscrizione
        cur.execute("SELECT * FROM subscriptions WHERE user_name = %s AND citta = %s", (user_name, citta))
        subscription = cur.fetchone()

        if not subscription:
            return jsonify({'error': 'Sottoscrizione non trovata'}), 404
        
        # Aggiorna la sottoscrizione con le nuove condizioni
        cur.execute("UPDATE subscriptions SET condizioni = %s WHERE user_name = %s AND citta = %s",
                    (json.dumps(nuove_condizioni), user_name, citta))
        conn.commit()

        return jsonify({'message': 'Sottoscrizione aggiornata con successo!'}), 200

    except Exception as e:
        conn.rollback()  # Annulla la transazione in caso di errore
        logging.error(f"Errore durante l'aggiornamento della sottoscrizione: {e}")
        return jsonify({'error': f"Errore durante l'aggiornamento della sottoscrizione: {e}"}), 500


# @app.route('/add_sla_metric', methods=['POST'])
# def add_sla_metric():
#     data = request.get_json()
#     metric_name = data['metric_name']
#     threshold = data['threshold']
#     description = data['description']
    
#     cur.execute("INSERT INTO sla_definitions (metric_name, threshold, description) VALUES (%s, %s, %s)",
#                 (metric_name, threshold, description))
#     conn.commit()
    
#     return jsonify({'message': 'SLA metric added successfully'}), 201

@app.route('/get_sla_metrics', methods=['GET'])
def get_sla_metrics():
    try:
        cur.execute("SELECT * FROM sla_definitions")
        sla_metrics = cur.fetchall()
        
        # Converti i risultati in un formato più leggibile/maneggevole
        sla_metrics_list = []
        for metric in sla_metrics:
            sla_metrics_list.append({
                'sla_id': metric[0],
                'metric_name': metric[1],
                'threshold': metric[2],
                'description': metric[3]
            })
        
        logging.info(f"SLA_metrics: {sla_metrics_list}")
        return jsonify(sla_metrics_list), 200
    except Exception as e:
        logging.error(f"Errore durante il recupero delle metriche SLA: {e}")
        return jsonify({'error': f"Errore durante il recupero delle metriche SLA: {e}"}), 500


@app.route('/update_sla_metric', methods=['PUT'])
def update_sla_metric():
    data = request.get_json()
    sla_id = data['sla_id']
    metric_name = data['metric_name']
    threshold = data['threshold']
    description = data['description']
    
    cur.execute("UPDATE sla_definitions SET metric_name = %s, threshold = %s, description = %s WHERE sla_id = %s",
                (metric_name, threshold, description, sla_id))
    conn.commit()
    
    return jsonify({'message': 'SLA metric updated successfully'}), 200

@app.route('/delete_sla_metric', methods=['DELETE'])
def delete_sla_metric():
    data = request.get_json()
    sla_id = data['sla_id']
    
    cur.execute("DELETE FROM sla_definitions WHERE sla_id = %s", (sla_id,))
    conn.commit()
    
    return jsonify({'message': 'SLA metric deleted successfully'}), 200

@app.route('/record_sla_violation', methods=['POST'])
def record_sla_violation():
    data = request.get_json()
    sla_id = data['sla_id']
    violation_time = data['violation_time']
    actual_value = data['actual_value']
    logging.info(f"Record: {actual_value}, {violation_time} ")
    
    cur.execute("INSERT INTO sla_violations (sla_id, violation_time, actual_value) VALUES (%s, %s, %s)",
                (sla_id, violation_time, actual_value))
    conn.commit()
    
    return jsonify({'message': 'SLA violation recorded successfully'}), 201

@app.route('/get_sla_violations', methods=['GET'])
def get_sla_violations():
    cur.execute("SELECT * FROM sla_violations")
    sla_violations = cur.fetchall()
    return jsonify(sla_violations), 200

@app.route('/add_sla_metric', methods=['POST'])
def add_sla_metric():
    # Ottenere i dati dalla richiesta
    data = request.get_json()
    metric_name = data.get('metric_name')
    threshold = data.get('threshold')
    description = data.get('description')

    # Verificare che tutti i campi necessari siano presenti
    if not all([metric_name, threshold, description]):
        return jsonify({'error': 'Mancano dati necessari per aggiungere una metrica SLA.'}), 400

    try:
        # Inserire i dati nella tabella sla_definitions
        cur.execute("""
            INSERT INTO sla_definitions (metric_name, threshold, description)
            VALUES (%s, %s, %s)
            """, (metric_name, threshold, description))
        conn.commit()
        return jsonify({'message': 'Metrica SLA aggiunta con successo'}), 201
    except psycopg2.Error as e:
        # Gestire gli errori del database, ad esempio violazioni della chiave univoca
        conn.rollback()  # Annullare la transazione in caso di errore
        return jsonify({'error': f"Errore durante l'aggiunta della metrica SLA: {e}"}), 500

# In database_service

@app.route('/count_sla_violations', methods=['GET'])
def count_sla_violations():
    time_frame = request.args.get('time_frame', default='1h')  # Può essere '1h', '3h', '6h'
    try:
        query = f"""
            SELECT COUNT(*) FROM sla_violations 
            WHERE violation_time >= NOW() - INTERVAL '{time_frame}'
        """
        cur.execute(query)
        count = cur.fetchone()[0]
        return jsonify({'time_frame': time_frame, 'violations_count': count}), 200
    except Exception as e:
        return jsonify({'error': f"Errore durante la richiesta del conteggio delle violazioni SLA: {e}"}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5004)



