import os, time
from db_scripts.db_operations import *
from telegram import Bot
import asyncio
from other_functions import *

host = os.environ.get('POSTGRES_HOST', 'NO VARIABLE POSTGRES_HOST')
user = os.environ.get('POSTGRES_USER', 'NO VARIABLE POSTGRES_USER')
password = os.environ.get('POSTGRES_PASSWORD', 'NO VARIABLE POSTGRES_PASSWORD')
database = os.environ.get('POSTGRES_DATABASE', 'NO VARIABLE POSTGRES_DATABASE')

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN_FILE", "NO_VARIABLE_FOUND")

time.sleep(10)

user_states = {}

def send_message(chat_id, text):
    bot_token = TELEGRAM_TOKEN
    # Creo un oggetto Bot
    bot = Bot(token=bot_token)
    # Invio il messaggio
    bot.send_message(chat_id=chat_id, text=text)

# Funzione asincrona per inviare le notifiche all'utente
async def send_message_async(chat_id, text):
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=chat_id, text=text)
    
# Funzione per gestire la conversazione dopo la scelta dell'intervallo di tempo dell'utente
def handle_subscription(chat_id, tmp, city_name, interval_seconds, sub_period):
    # Imposto il valore desiderato in minuti
    sub_period_seconds = sub_period * 60  # Conversione in secondi

    start_time = time.time()
    end_time = start_time + sub_period_seconds  # Calcolo il tempo di fine
    while time.time() < end_time:
        # Verifico se l'utente ha richiesto di fermare le notifiche
        if user_states.get(chat_id) == 'stop':
            send_message(chat_id, text="Hai interrotto le notifiche.")
            break

        # Invio messaggio ogni notify_freq secondi
        text=f"Interval event: {interval_seconds} seconds. Current weather in {city_name}: {tmp}"
        asyncio.run(send_message_async(chat_id, text))

        time.sleep(interval_seconds)
        
        
        
conn, cur = initialize_database_connection(host, user, password, database)
svuota_tabelle(conn, cur)

old_mappa_ricerche = None
while True:
    try:
        conn, cur = initialize_database_connection(host, user, password, database)

        nuova_mappa_ricerche, last_search = leggi_ricerche(cur)
        
        # Se la nuova mappa non è uguale alla vecchia mappa allora è stata 
        # effettuata una nuova sottoscrizione.
        if nuova_mappa_ricerche != old_mappa_ricerche and nuova_mappa_ricerche:
            city_id = ""
            sub_period = 0
            notify_freq = 0

            sub_period = last_search[2]
            notify_freq = last_search[3]
            chat_id = get_chat_id_for_user(cur, last_search[0])
            city_name, city_constraints = get_city_info(cur, last_search[1])      

            # Richiesta meteo al sito openWeatherMap
            info_weather = return_weather(city_name)

            # Usiamo il file prova.txt solo per dei test
            with open("db_scripts/prova.txt", 'w') as file_output:
                file_output.write(f"City_id: {last_search[1]}, user_id {last_search[0]}, sub_period{last_search[2]}")

                
            info_weather_constraint = select_constraint_from_info_weather(info_weather, city_constraints)
                
            handle_subscription(chat_id, info_weather_constraint, city_name, notify_freq, sub_period)

            # Aggiorno la vecchia mappa con la nuova mappa
            old_mappa_ricerche = nuova_mappa_ricerche
        else:
            print("Nessuna nuova ricerca effettuata!")
    finally:
        # Chiudo la connessione al database alla fine di ogni ciclo
        close_database_connection(conn, cur)

