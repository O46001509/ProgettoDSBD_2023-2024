from flask import Flask, request, jsonify, abort, Response
# from telegram import Update
# from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import time, os
import requests
import logging
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Histogram
from prometheus_client import Counter
from prometheus_client.exposition import generate_latest

# Inizializzazione del logging
logging.basicConfig(level=logging.INFO)  # Imposta il livello di logging a INFO

time.sleep(4)

app = Flask(__name__)

DATABASE_SERVICE_URL = "http://database-service:5004"
# TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN_FILE", "NO_VARIABLE_FOUND")

# # Configura le metriche Prometheus
metrics = PrometheusMetrics(app)

# Aggiungi metriche personalizzate
metrics.info("app_info", "Application info", version="1.0.0")
@app.route('/')
def home():
    return 'Weather Event Notifier'

@app.route('/metrics')
def metrics():
    # Restituisci le metriche Prometheus
    return Response(generate_latest(), mimetype='text/plain')

subscriptions = {}
user_states = {}

# # Aggiungi una metrica per la frequenza di recupero dati meteorologici
fetch_weather_counter = Counter(
    'fetch_weather_requests',
    'Number of requests to fetch weather data'
)

# Aggiungi una metrica per i tempi di risposta delle richieste alle API meteorologiche
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

@app.route('/sottoscrizioni', methods=['GET', 'POST','DELETE','PUT'])
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
            user_name = data.get('user_name')
            citta = data.get('citta')

            # Verifica se esiste già una sottoscrizione per l'utente e la città
            subscription_exists_url = f"{DATABASE_SERVICE_URL}/verifica_sottoscrizione"
            subscription_exists_data = {'user_name': user_name, 'citta': citta}
            subscription_exists_response = requests.post(subscription_exists_url, json=subscription_exists_data)

            if subscription_exists_response.status_code == 200:
                # Sottoscrizione esistente, restituisci errore
                return jsonify({'error': "Esiste gi\u00E0 una sottoscrizione per questa citt\u00E0 per l'utente specificato. Si prega di inserire una nuova citt\u00E0 o aggiornare la sottoscrizione esistente."}), 400
            elif subscription_exists_response.status_code == 404:
                #  # Incrementa la metrica per la frequenza di recupero dati meteorologici
                fetch_weather_counter.inc()

                start_time = time.time()

                chat_id_service_url = f'{DATABASE_SERVICE_URL}/chat_id?user_name={user_name}'
                chat_id_response = requests.get(chat_id_service_url)

                if chat_id_response.status_code == 200:
                    chat_id_data = chat_id_response.json()

                    user_exists_response = requests.get(f"{DATABASE_SERVICE_URL}/recupera_utente", params={'user_name': user_name, 'chat_id': chat_id_data['decrypted_chat_id']})
                    user_exists_data = user_exists_response.json()

                    if not user_exists_data:
                        #  interruzione immediata dell'esecuzione dell'endpoint /sottoscrizioni
                        abort(400, {'error': 'Utente non trovato nel database. Registrati, pigiando il coamndo start nel bot telegram "giosa-weather-alerts", prima di creare una sottoscrizione.'})

                    # L'utente è presente, procedi con la creazione della sottoscrizione
                    response = requests.post(f"{DATABASE_SERVICE_URL}/sottoscrizioni", json=data)
                    response.raise_for_status()
                    logging.info("Sottoscrizione creata con successo")

                    # # Misura il tempo di risposta e aggiorna la metrica
                    duration = time.time() - start_time
                    fetch_weather_duration.observe(duration)

                    return jsonify({'message': 'Sottoscrizione creata con successo!'}), 201
                else:
                    return jsonify({'error': 'La sottoscrizione non creata: id non trovato'}), 404
            else:
                # Errore imprevisto durante la verifica dell'esistenza della sottoscrizione
                return jsonify({'error': 'Errore durante la verifica dell\'esistenza della sottoscrizione'}), 500

        except requests.exceptions.RequestException as e:
            logging.error(f"Errore durante la creazione della sottoscrizione: {e}")
            abort(500, {'error': 'Errore durante la creazione della sottoscrizione.'})
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            user_name = data.get('user_name')
            citta = data.get('citta')
            # Assumi che "nuove_condizioni" sia il campo con le nuove informazioni per la sottoscrizione
            nuove_condizioni = data.get('nuove_condizioni')

            # Verifica se esiste già una sottoscrizione per l'utente e la città
            subscription_exists_url = f"{DATABASE_SERVICE_URL}/verifica_sottoscrizione"
            subscription_exists_data = {'user_name': user_name, 'citta': citta}
            subscription_exists_response = requests.post(subscription_exists_url, json=subscription_exists_data)

            if subscription_exists_response.status_code == 200:
                # La sottoscrizione esiste, procedi con l'aggiornamento
                update_data = {
                    'user_name': user_name,
                    'citta': citta,
                    'nuove_condizioni': nuove_condizioni
                }
                update_response = requests.put(f"{DATABASE_SERVICE_URL}/aggiorna_sottoscrizione", json=update_data)
                if update_response.status_code == 200:
                    return jsonify({'message': 'Sottoscrizione aggiornata con successo!'}), 200
                else:
                    return jsonify({'error': 'Errore durante l\'aggiornamento della sottoscrizione'}), update_response.status_code

            elif subscription_exists_response.status_code == 404:
                # La sottoscrizione non esiste, restituisci errore
                return jsonify({'error': 'Sottoscrizione non trovata per aggiornamento'}), 404
            else:
                # Errore imprevisto durante la verifica dell'esistenza della sottoscrizione
                return jsonify({'error': 'Errore durante la verifica dell\'esistenza della sottoscrizione'}), 500

        except requests.exceptions.RequestException as e:
            logging.error(f"Errore durante l'aggiornamento della sottoscrizione: {e}")
            abort(500, {'error': "Errore durante l'aggiornamento della sottoscrizione."})
    elif request.method == 'DELETE':
        # Cancellazione di una sottoscrizione
        try:
            data = request.get_json()

            # Verifica se l'utente e la città sono specificati
            user_name = data.get('user_name')
            citta = data.get('citta')

            if not user_name or not citta:
                return jsonify({'error': 'Specificare user_name e citta come parametri nella richiesta'}), 400

            # Verifica se la sottoscrizione esiste
            subscription_exists_url = f"{DATABASE_SERVICE_URL}/verifica_sottoscrizione"
            subscription_exists_data = {'user_name': user_name, 'citta': citta}
            subscription_exists_response = requests.post(subscription_exists_url, json=subscription_exists_data)

            if subscription_exists_response.status_code == 200:
                # La sottoscrizione esiste, procedi con la cancellazione
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






