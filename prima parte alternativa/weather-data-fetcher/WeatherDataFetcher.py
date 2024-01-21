import requests
import time, os
import datetime as dt
from openweather_wrapper import OpenWeatherWrapper

time.sleep(5)

# Funzione per ottenere l'istante di tempo attuale
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


def fetch_weather_data(city):
    tmp = return_weather(city)[1]
    fl_tmp = return_weather(city)[2]
    wind_speed = return_weather(city)[3]
    hum = return_weather(city)[4]
    general = return_weather(city)[5]
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

# Verifica delle condizioni specificate nella sottoscrizione sono soddisfatte
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
def main():
    while True:
        # Recuperiamo le sottoscrizioni dal Weather Event Notifier
        subscriptions_url = 'http://weather-event-notifier:5001/sottoscrizioni'
        subscriptions_response = requests.get(subscriptions_url)

        if subscriptions_response.status_code == 200:
            subscriptions = subscriptions_response.json()
            print(f"{subscriptions}")
            # for subscription in subscriptions: #ciclo per eventualmente gestire più sottoscrizioni
                                                # da parte di un utente.
            if subscriptions:
                
                print(f"{subscriptions.keys()}")
                chat_id = list(subscriptions.keys())[0]
                city = subscriptions[chat_id]['citta']
                weather_data = fetch_weather_data(city)

                if check_conditions(subscriptions[chat_id], weather_data):
                    # Se le condizioni sono soddisfatte, invia una richiesta al Notification Server
                    notification_data = {
                        'user_id': chat_id,
                        'message': f"Condizioni meteorologiche soddisfatte a {city} - Temperatura: {weather_data['temperature']:.2f}°C,"
                                   f"Temperatura percepita: {weather_data['feel_temperature']:.2f}°C,"
                                    f"Umidita': {weather_data['humidity']}%,"
                                    f"Meteo generale: {weather_data['general_weather']},"
                                    f"Velocita' del vento: {(weather_data['wind_speed']*3.6):.2f}km/h\n"
                                    f"{stampa_ora_attuale()}"
                    }

                    # Invia la richiesta al Notification Server
                    notification_url = 'http://notification-service:5000/notifiche'
                    headers = {'Content-Type': 'application/json'}
                    requests.post(notification_url, json=notification_data, headers=headers)

        # Simula un intervallo di 10 minuti tra le verifiche meteorologiche, cioè
        # la frequenza con cui mandare l'info meteo all'utente - in questo caso 10 secondi ma
        # potrebbe essere impostata realmente a 10 minuti o 1 ora, ecc...
        time.sleep(10)

if __name__ == '__main__':
    main()






