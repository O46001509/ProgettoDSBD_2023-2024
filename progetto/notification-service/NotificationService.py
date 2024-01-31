from flask import Flask, request, jsonify, Response
from telegram import Bot, error
from telegram.constants import ParseMode
import asyncio, os, logging, time
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import generate_latest
import threading
import requests
from timelocallogging_wrapper import LocalTimeFormatter


# ---------------------------------------------------
formatter = LocalTimeFormatter(
    fmt='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)
# ---------------------------------------------------


app = Flask(__name__)

# Inizializzo il contatore di allerte Memoria usata da un container 
# e il lock per l'accesso sicuro tra thread usati per misurarlo.
alert_counter = 0
counter_lock = threading.Lock()

metrics = PrometheusMetrics(app)

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype='text/plain')

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN_FILE", "NO_VARIABLE_FOUND")

# metodo asincrono per gestire l'invio di più notifiche
async def send_telegram_notification(chat_id, message):
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.MARKDOWN)

@app.route('/notifiche', methods=['POST'])
def receive_notification():
    data = request.get_json()
    user_id = data.get('user_id')  # Qui si ottiene il chat_id dell'utente
    message = data.get('message')
    #print(f"Richiesta ricevuta - User ID: {user_id}, Messaggio: {message}")

    # delay di 1 secondo per velocizzare il verificarsi di allerte.
    time.sleep(1)

    asyncio.run(send_telegram_notification(user_id, message))
    return jsonify({'message': 'Notifica inviata con successo!'}), 200

# Imposta il timer per il reset del contatore
# nel caso in cui non arrivano altre allerte.
ALERT_INTERVAL = 180  # 2 minuti
alert_timer = None

def reset_counter():
    global alert_counter, alert_timer
    with counter_lock:
        alert_counter = 0
        alert_timer = None
        logger.info("Contatore di allerte resettato per inattività.")

# Per ora abbiamo deciso di gestire l'intervallo di un solo
# utente ma si potrebbero gestire anche altri intervalli
# di altri utenti, inserendo la gestione degli job anche nel
# weather-data-fetcher. 
def recupera_intervallo_primo_utente():
    url = "http://database-service:5004/recupera_intervallo_primo_utente"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            intervallo = data['intervallo']
            logger.info(f"Intervallo recuperato per il primo utente: {intervallo}")
            return intervallo
        else:
            logger.error(f"Errore durante il recupero dell'intervallo: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Errore durante la richiesta all'endpoint /recupera_intervallo_primo_utente: {e}")
        return None


def aggiorna_intervallo_tutti(nuovo_intervallo):
    url = "http://database-service:5004/aggiorna_intervallo_tutti"
    data = {"nuovo_intervallo": nuovo_intervallo}
    response = requests.put(url, json=data)
    if response.status_code == 200:
        logger.info("Intervallo aggiornato con successo per tutti gli utenti")
    else:
        logger.error(f"Errore durante l'aggiornamento dell'intervallo: {response.text}")

# Numero di allarmi dopo il quale aggiornare l'intervallo notifiche, 
# in modo da compiere un'azione correttiva automatica nel caso
# di violazione della metrica SLA notification_interval_seconds.
ALERT_COUNT_THRESHOLD = 3  
PERCENTAGE_INCREMENT = 10  # Percentuale di incremento dell'intervallo

# viene notificata l'allerta all'utente.
@app.route('/alert', methods=['POST'])
def receive_alert():
    global alert_counter, alert_timer
    
    try:
        data = request.get_json()
        alerts = data.get('alerts', [])

        user_name_url = f'http://database-service:5004/recupera_primo_user_name'
        user_name_response = requests.get(user_name_url)
        user_name_data = user_name_response.json()
        user_n = user_name_data['user_name']
        user_name_response.raise_for_status()

        chat_id_url = f'http://weather-event-notifier:5001/chat_id?user_name={user_n}'
        chat_id_response = requests.get(chat_id_url)
        chat_id_response.raise_for_status()
        chat_id = chat_id_response.json().get('decrypted_chat_id')

        for alert in alerts:
            # Ottieni informazioni dall'allarme
            alertname = alert['labels'].get('alertname', 'Unknown')
            instance = alert['labels'].get('instance', 'Unknown')
            summary = alert['annotations'].get('summary', 'No details')
            message = f"ALERT: {alertname} Limite massimo delle sottoscrizioni raggiunto:intervallo notifiche scelto non rispettato.\n Per tornare in uno stato di normalità elimina qualche sottoscrizione, altrimenti dopo 3 ALERT il sistema si auto-aggiusterà incrementado l'intervallo del 10%"

            user_id = chat_id 

            # Invio la notifica a Telegram, se user_id è presente
            if user_id:
                
                try:
                    asyncio.run(send_telegram_notification(user_id, message))
                    with counter_lock:
                        # Incrementa il contatore per ogni batch di allerte ricevute
                        alert_counter += len(alerts)
                        logger.info(f"Allerte ricevute: {len(alerts)}. Totale allerte ricevute finora: {alert_counter}")
                        logger.info(f"Counter_lock --> {counter_lock}")

                        # Resetta il timer per il prossimo reset del contatore
                        if alert_timer:
                            alert_timer.cancel()
                        alert_timer = threading.Timer(ALERT_INTERVAL, reset_counter)
                        alert_timer.start()
                    if alert_counter >= ALERT_COUNT_THRESHOLD:
                        current_interval = recupera_intervallo_primo_utente()
                        if current_interval is not None:
                            # Calcola il nuovo intervallo incrementato del 10%
                            nuovo_intervallo = current_interval * (1 + PERCENTAGE_INCREMENT / 100)
                            # Aggiorna l'intervallo per tutti gli utenti
                            aggiorna_intervallo_tutti(nuovo_intervallo)
                            # Resetta il contatore degli allarmi
                            alert_counter = 0
                except error.RetryAfter as e:
                    '''
                        Se l'intervallo notifiche viene scelto troppo piccolo o vengono effettuate troppo 
                        sottoscrizioni, i troppi messaggi che arriveranno al bot verranni visti come spam
                        e per continuare ad usare il sistema, si deve aspettare il tempo stabilito (retry_after).
                        Questo si può vedere direttamente nella chat col bot che non invierà più nessu messaggio.
                        Se si verifica, provare a eliminare dal db (secondo la query e i comandi presenti nella
                        sezione "Installazione e Configurazione: 5. Inizializzazione e risoluzione di eventuali 
                        interruzioni del Database:" del file Readme, presente sul repository GitHub fornito 
                        da noi) tutte le sottoscrizioni e riavviare il sistema stesso. Se ancora non funziona,
                        testare da un altro profilo telegram.
                    '''
                    logger.info(f"Inviati messaggi troppo rapidamente. Aspettare {e.retry_after} secondi.")
                    time.sleep(e.retry_after)  # Aspetto per il tempo consigliato prima di riprovare
                    asyncio.run(send_telegram_notification(user_id, message))

                logger.info("Avviso violazione SLA inviato con successo")
            else:
                print(f"UserID non trovato per l'allarme: {message}")

        return jsonify({'message': 'Notifica inviata con successo!'}), 200
    except Exception as e:
        logger.error(f"Errore recupero user_name o altro: {e}") 
        return jsonify({'error': 'An error occurred', 'details': str(e)}), 500

app.add_url_rule('/alert', 'receive_alert', receive_alert, methods=['POST'])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)




