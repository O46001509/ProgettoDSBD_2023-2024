from flask import Flask, request, jsonify, abort, Response
import time, os
import requests
import logging
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Histogram
from prometheus_client import Counter
from prometheus_client.exposition import generate_latest

logging.basicConfig(level=logging.INFO)  # Imposto il livello di logging a INFO

time.sleep(4)

app = Flask(__name__)

DATABASE_SERVICE_URL = "http://database-service:5004"
# TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN_FILE", "NO_VARIABLE_FOUND")

# Configuro le metriche Prometheus
metrics = PrometheusMetrics(app)

# Esempio aggiunta metrica personalizzata
metrics.info("app_info", "Application info", version="1.0.0")
@app.route('/')
def home():
    return 'Weather Event Notifier'

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype='text/plain')

subscriptions = {}
user_states = {}

# metrica per la frequenza di recupero dati meteorologici
fetch_weather_counter = Counter(
    'fetch_weather_requests',
    'Number of requests to fetch weather data'
)

# metrica per i tempi di risposta delle richieste alle API meteorologiche
fetch_weather_duration = Histogram(
    'fetch_weather_duration_seconds',
    'Duration of fetch weather requests',
    buckets=[0.1, 0.5, 1, 2, 10]
)

# Funzione per creare la tabella degli utenti
def create_users_table():
    try:
        response = requests.post(f"{DATABASE_SERVICE_URL}/crea_tabella_utenti")
        response.raise_for_status()  # Solleva un'eccezione per codici di stato HTTP diversi da 2xx
        logging.info("Tabella degli utenti creata con successo")
    except requests.exceptions.RequestException as e:
        logging.error(f"Errore durante la creazione della tabella degli utenti: {e}")

# Funzione per creare la tabella delle sottoscrizioni
def create_subscriptions_table():
    try:
        response = requests.post(f"{DATABASE_SERVICE_URL}/crea_tabella_sottoscrizioni")
        response.raise_for_status()
        logging.info("Tabella delle sottoscrizioni creata con successo")
    except requests.exceptions.RequestException as e:
        logging.error(f"Errore durante la creazione della tabella delle sottoscrizioni: {e}")

def get_subscriptions():
    try:
        response = requests.get(f"{DATABASE_SERVICE_URL}/sottoscrizioni")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # Gestire l'errore o loggarlo
        print(f"Errore durante la richiesta delle sottoscrizioni: {e}")
        return []

create_users_table()
create_subscriptions_table()

@app.route('/sottoscrizioni', methods=['GET', 'POST','DELETE'])
def manage_subscriptions():
    if request.method == 'GET':
        try:
            user_name = request.args.get('user_name')

            if not user_name:
                return jsonify({'error': 'Specificare user_name come parametro nella richiesta'}), 400

            subscription_service_url = f'{DATABASE_SERVICE_URL}/sottoscrizioni?user_name={user_name}'
            subscription_response = requests.get(subscription_service_url)

            if subscription_response.status_code == 200:
                subscriptions = subscription_response.json()
                return jsonify(subscriptions), 200
            else:
                return jsonify({'error': f"Errore durante la richiesta delle sottoscrizioni: {subscription_response.text}"}), 500

        except Exception as e:
            return jsonify({'error': f"Errore durante la richiesta delle sottoscrizioni: {e}"}), 500

    elif request.method == 'POST':
        # Creazione di una nuova sottoscrizione
        try:
            data = request.get_json()
            
            # Incrementa la metrica per la frequenza di recupero dati meteorologici
            fetch_weather_counter.inc()
            start_time = time.time()

            # Verifica se l'utente è già presente nel database
            user_name = data.get('user_name')
            chat_id = data.get('chat_id')
            user_exists_response = requests.get(f"{DATABASE_SERVICE_URL}/recupera_utente", params={'user_name': user_name, 'chat_id': chat_id})
            user_exists_data = user_exists_response.json()

            if not user_exists_data:
                #  interruzione immediata dell'esecuzione dell'endpoint /sottoscrizioni
                abort(400, {'error': 'Utente non trovato nel database. Registrati, pigiando il coamndo start nel bot telegram "giosa-weather-alerts", prima di creare una sottoscrizione.'})

            # L'utente è presente, procedi con la creazione della sottoscrizione
            response = requests.post(f"{DATABASE_SERVICE_URL}/sottoscrizioni", json=data)
            response.raise_for_status()
            logging.info("Sottoscrizione creata con successo")

            # Misura il tempo di risposta e aggiorna la metrica
            duration = time.time() - start_time
            fetch_weather_duration.observe(duration)

            return jsonify({'message': 'Sottoscrizione creata con successo!'}), 201

        except requests.exceptions.RequestException as e:
            logging.error(f"Errore durante la creazione della sottoscrizione: {e}")
            abort(500, {'error': 'Errore durante la creazione della sottoscrizione.'})
    elif request.method == 'DELETE':
        # Cancellazione di una sottoscrizione
        try:
            data = request.get_json()

            # Verifico se l'utente e la città sono specificati
            user_name = data.get('user_name')
            city = data.get('citta')

            if not user_name or not city:
                return jsonify({'error': 'Specificare user_name e citta come parametri nella richiesta'}), 400

            # Verifico se la sottoscrizione esiste
            subscription_exists_url = f"{DATABASE_SERVICE_URL}/verifica_sottoscrizione"
            subscription_exists_data = {'user_name': user_name, 'citta': city}
            subscription_exists_response = requests.post(subscription_exists_url, json=subscription_exists_data)

            if subscription_exists_response.status_code == 200:
                # La sottoscrizione esiste, procedo con la cancellazione
                delete_subscription_url = f"{DATABASE_SERVICE_URL}/cancella_sottoscrizione"
                delete_subscription_response = requests.post(delete_subscription_url, json=subscription_exists_data)
                
                if delete_subscription_response.status_code == 200:
                    return jsonify({'message': 'Sottoscrizione cancellata con successo!'}), 200
                else:
                    return jsonify({'error': f"Errore durante la cancellazione della sottoscrizione: {delete_subscription_response.text}"}), 500

            else:
                # La sottoscrizione non esiste
                return jsonify({'error': 'La sottoscrizione non esiste'}), 404

        except requests.exceptions.RequestException as e:
            logging.error(f"Errore durante la cancellazione della sottoscrizione: {e}")
            abort(500, {'error': 'Errore durante la cancellazione della sottoscrizione.'})
    
@app.route('/utenti', methods=['GET'])
def get_user_names():
    try:
        response = requests.get(f"{DATABASE_SERVICE_URL}/utenti_user_name")
        response.raise_for_status()
        user_names = response.json()
        return jsonify(user_names), 200
    except requests.exceptions.RequestException as e:
        logging.error(f"Errore durante la richiesta degli user_name: {e}")
        return jsonify({'error': f"Errore durante la richiesta degli user_name: {e}"}), 500
    
@app.route('/chat_id', methods=['GET'])
def get_chat_id_by_user_name():
    try:
        user_name = request.args.get('user_name')

        if not user_name:
            return jsonify({'error': 'Specificare user_name come parametro nella richiesta'}), 400

        chat_id_service_url = f'{DATABASE_SERVICE_URL}/chat_id?user_name={user_name}'
        chat_id_response = requests.get(chat_id_service_url)

        if chat_id_response.status_code == 200:
            chat_id_data = chat_id_response.json()
            logging.info(f"chat_id recuperato{chat_id_data['decrypted_chat_id']} + result {chat_id_response}")
            return jsonify({'decrypted_chat_id': chat_id_data['decrypted_chat_id']}), 200
        else:
            return jsonify({'error': f"Errore durante la richiesta del chat_id: {chat_id_response.text}"}), 500

    except Exception as e:
        return jsonify({'error': f"Errore durante la richiesta del chat_id: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)






