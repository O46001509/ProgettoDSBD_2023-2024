import requests
import os, logging, time
from openweather_wrapper import OpenWeatherWrapper

from prometheus_client import Gauge
from prometheus_client.exposition import generate_latest

from flask import Flask, Response

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError

from timelocallogging_wrapper import LocalTimeFormatter



DATABASE_SERVICE_URL = "http://database-service:5004"

# Lettura dell'intervallo notifiche iniziale (all'avvio del sistema)
with open("intervallo.txt", 'r') as file:
    contenuto = file.read()
    INTERVALLO_NOTIFICHE = int(contenuto)

# Variabile e struttura dati per calcolare il tempo 
# effettivo tra una richiesta e l'altra.
last_first_notification_time = None
last_notification_time = {}

# --------------------------------------------------
formatter = LocalTimeFormatter(
    fmt='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)
# --------------------------------------------------

# attesa nel caso in cui l'event-notifier debba ancora avviarsi, 
# perché sta attendendo il database-service.
time.sleep(5)

app = Flask(__name__)

# Creazione metrica che può essere selezionata dall'UI di Prometheus
# come notification_interval_seconds,
# per visualizzare l'intervallo effettivo di arrivo notifiche. 
notification_interval_gauge = Gauge(
    'notification_interval_seconds',
    'Effective interval between notifications in seconds'
)

@app.route('/metrics')
def metrics():
    # Restituisco le metriche Prometheus
    return Response(generate_latest(), mimetype='text/plain')

# Funzione per ottenere l'istante di tempo attuale
# e indicarlo nella notifica inviata tramite bot Telegram.
def stampa_ora_attuale():
    ora_attuale_struct = time.localtime()

    ora_attuale = ora_attuale_struct.tm_hour+1
    minuti_attuali = ora_attuale_struct.tm_min
    secondi_attuali = ora_attuale_struct.tm_sec
    return f'Current time: {ora_attuale:02d}:{minuti_attuali:02d}:{secondi_attuali:02d}'

# Funzione che elabora e ritorna le info ottenute da OpenWeatherMap
def return_weather(city):
    API_KEY = os.environ.get("OPENWEATHERMAP_API_KEY_FILE", "NO_VARIABLE_FOUND")

    weather_wrapper = OpenWeatherWrapper(API_KEY)
    response = weather_wrapper.get_weather_data(city) 

    if response:
        # Conversione da kelvin a celsisus e fahrenheit
        def kelvin_to_celsius_fahrenheit(kelvin):
            celsius = kelvin - 273.15
            fahrenheit = celsius * (9/5) + 32
            return celsius, fahrenheit

        temp_kelvin = response['main']['temp']
        temp_celsius, temp_fahr = kelvin_to_celsius_fahrenheit(temp_kelvin)

        feels_like_kelvin = response['main']['feels_like']
        fl_celsius, fl_fahr = kelvin_to_celsius_fahrenheit(feels_like_kelvin)

        wind_speed = response['wind']['speed']
        #sunrise_time = dt.datetime.utcfromtimestamp(response['sys']['sunrise'] + response['timezone'])
        #sunset_time = dt.datetime.utcfromtimestamp(response['sys']['sunset'] + response['timezone'])

        humidity = response['main']['humidity']
        description = response['weather'][0]['description']

        info_meteo = [
        city, temp_celsius, fl_celsius, wind_speed, humidity, description
        ]
        return info_meteo

    else:
        info_meteo = None
        return info_meteo

def fetch_weather_data(city):
    info_meteo = return_weather(city)
    if info_meteo:
        tmp = info_meteo[1]
        fl_tmp = info_meteo[2]
        wind_speed = info_meteo[3]
        hum = info_meteo[4]
        general = info_meteo[5]
        # Restituisce dati meteorologici di esempio per la città specificata
        return {
            'citta': city,
            'temperature': tmp,
            'feel_temperature': fl_tmp,
            'wind_speed': wind_speed,
            'humidity' : hum,
            'general_weather': general,
            # 'rainfall': 5,      # Quantità di pioggia di esempio in mm
            # 'snowfall': 0       # Quantità di neve di esempio in mm
        }
    else:
        return None
    
# Verifica che le condizioni specificate nella sottoscrizione sono soddisfatte.
def check_conditions(subscription, weather_data):
    temperature_max = subscription['condizioni']['temperatura_massima']
    temperatura_minima = subscription['condizioni']['temperatura_minima']
    vento_max = subscription['condizioni']['vento_max']
    umidita_max = subscription['condizioni']['umidita_max']
    return ( 
            weather_data['temperature'] <= temperature_max and
            weather_data['temperature'] >= temperatura_minima and
            (weather_data['wind_speed'])*3.6 <= vento_max and
            weather_data['humidity'] <= umidita_max
    )

'''
Pianificazione del job main per eseguire periodicamente
la logica del servizio weather-data-fetcher: acquisire 
l'intervallo effettivo (ed eventualmente modificarlo), 
verificare le condizioni per ogni sottoscrizione effettuata
e inviare al notification-service le notifiche.
'''
def add_main_job(scheduler, seconds):
    try:
        scheduler.remove_job('main_job')  # Rimuovo il job se esiste
    except JobLookupError:
        pass  # Se il job non esiste
    scheduler.add_job(main, 'interval', seconds=seconds, id='main_job')

def main():
    global last_first_notification_time
    global INTERVALLO_NOTIFICHE
    is_first_subscription = True

    try:
        # Recuperiamo gli user_name dal Weather Event Notifier
        user_names_url = 'http://weather-event-notifier:5001/utenti'
        user_names_response = requests.get(user_names_url)
        user_names_response.raise_for_status()
        logger.info(f"Weather-data-fetcher --> user_names_response: {user_names_response}")

        if user_names_response.status_code == 200:
            user_names = user_names_response.json()
            logger.info(f"User names: {user_names}")

            for user_name in user_names:
                # Recupero il chat_id per ogni user_name
                chat_id_url = f'http://weather-event-notifier:5001/chat_id?user_name={user_name}'
                chat_id_response = requests.get(chat_id_url)
                chat_id_response.raise_for_status()
                chat_id = chat_id_response.json().get('decrypted_chat_id')

                 # Recupero intervallo secondo il chat_id
                interval_url = f"{DATABASE_SERVICE_URL}/recupera_intervallo?chat_id={chat_id}"
                interval_response = requests.get(interval_url)
                interval_response.raise_for_status()
                interval = interval_response.json().get('interval')
                
                # Recupero le sottoscrizioni per ogni user_name
                subscriptions_url = f'http://weather-event-notifier:5001/sottoscrizioni?user_name={user_name}'
                subscriptions_response = requests.get(subscriptions_url)
                subscriptions_response.raise_for_status()

                if subscriptions_response.status_code == 200:
                    subscriptions = subscriptions_response.json()
                    INTERVALLO_NOTIFICHE = interval

                    # Scrittura dell'intervallo notifiche fornito da un utente
                    with open('intervallo.txt', 'w') as file:
                        file.write(str(interval))
                    add_main_job(scheduler, INTERVALLO_NOTIFICHE)
                    logger.info(f"Weather-data-fetcher --> INTERVALLO: {INTERVALLO_NOTIFICHE}")

                    # Processamento delle sottoscrizioni per l'utente corrente
                    logger.info(f"Subscriptions: {subscriptions}")
                    for subscription_info in subscriptions:
                
                        city = subscription_info['citta']
                        weather_data = fetch_weather_data(city)

                        # Se i dati restituiti dalla chiamata all'API di OpenWeatherMap sono corretti...
                        if weather_data:
                            logger.info(f"Weather-data-fetcher --> citta scelta: {city}")
                            # ...verifico le condizioni.
                            if check_conditions(subscription_info, weather_data):

                                # aggiornamento della metrica notification_interval_seconds
                                if is_first_subscription:
                                    is_first_subscription = False
                                    current_time = time.time()
                                    if last_first_notification_time is not None:
                                        interval = current_time - last_first_notification_time
                                        notification_interval_gauge.set(interval)
                                        logger.info(f"Weather-data-fetcher --> Intervallo effettivo tra le prime sottoscrizioni dei cicli: {interval} secondi")
                                    last_first_notification_time = current_time
                                logger.info(f"Weather-data-fetcher --> condizioni soddisfatte nella citta {city} cercata dall'utente {user_name}.")
                                
                                # Se le condizioni sono soddisfatte, invio una richiesta al Notification Server
                                notification_data = {
                                    'user_id': chat_id,
                                    'user_name': user_name,
                                    'message': f"Condizioni meteorologiche soddisfatte a {city} - Temperatura: {weather_data['temperature']:.2f}°C,"
                                            f"Temperatura percepita: {weather_data['feel_temperature']:.2f}°C,"
                                            f"Umidita': {weather_data['humidity']}%,"
                                            f"Meteo generale: {weather_data['general_weather']},"
                                            f"Velocita' del vento: {(weather_data['wind_speed']*3.6):.2f}km/h\n"
                                            f"{stampa_ora_attuale()}"
                                }

                                # Invio della richiesta al Notification Server
                                notification_url = 'http://notification-service:5000/notifiche'
                                headers = {'Content-Type': 'application/json'}
                                requests.post(notification_url, json=notification_data, headers=headers)
                            else:
                                logger.info(f"Weather-data-fetcher --> condizioni non soddisfatte nella citta {city} cercata dall'utente {user_name}.")
                        else:
                            logger.error("Nome della città scritto in modo sbagliato.")
                            subscription_exists_data = {
                                'user_name': user_name,
                                'citta': city
                            }
                            delete_subscription_url = f"{DATABASE_SERVICE_URL}/cancella_sottoscrizione"
                            delete_subscription_response = requests.post(delete_subscription_url, json=subscription_exists_data)
                            
                            if delete_subscription_response.status_code == 200:
                                logger.error({'message': 'Sottoscrizione, scritta sbagliata, cancellata con successo!'}), 200
                            else:
                                logger.error({'error': f"Errore durante la cancellazione della sottoscrizione, scritta sbagliata: {delete_subscription_response.text}"}), 500

    except requests.exceptions.ConnectionError as e:
        print(f"Errore di connessione: {e}")
    except requests.exceptions.HTTPError as e:
        print(f"Errore HTTP: {e}")
    except Exception as e:
        print(f"Errore sconosciuto: {e}")

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    # Esegue main() ogni INTERVALLO_NOTIFICHE secondi, in modo da garantire
    # la richiesta scelta dall'utente.
    scheduler.add_job(main,  'interval', seconds=INTERVALLO_NOTIFICHE, id='main_job')  
    scheduler.start()

    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5006)







