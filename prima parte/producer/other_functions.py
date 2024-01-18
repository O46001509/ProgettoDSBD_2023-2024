from kafka import KafkaProducer
import time, os
import datetime as dt
import requests

def return_weather(city):
    
    # Innanzitutto specifichiamo l'URL di base a cui inviamo le richieste
    BASE_URL = "http://api.openweathermap.org/data/2.5/weather?"
    
    # Leggi la chiave API dalla variabile di ambiente
    API_KEY = os.environ.get("OPENWEATHERMAP_API_KEY_FILE", "NO_VARIABLE_FOUND")
    # e la città di cui vogliamo ottenere i dati
    CITY = city

    url = BASE_URL + "appid=" + API_KEY + "&q=" + CITY
    # facciamo una richiesta
    response = requests.get(url).json()

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
    sunrise_time = dt.datetime.utcfromtimestamp(response['sys']['sunrise'] + response['timezone'])
    sunset_time = dt.datetime.utcfromtimestamp(response['sys']['sunset'] + response['timezone'])

    humidity = response['main']['humidity']
    description = response['weather'][0]['description']

    info_meteo = [
        f"Temperature in {CITY}: {temp_celsius:.2f}°C or {temp_fahr:.2f}°F",
        f"Temperature in {CITY} feels_like: {fl_celsius:.2f}°C or {fl_fahr:.2f}°F",
        f"Humidity in {CITY}: {humidity}%",
        f"General weather in {CITY}: {description}",
        f"Wind speed in {CITY}: {(wind_speed*3.6):.2f}km/h",
        f"Sun rises in {CITY} at {sunrise_time} local time.",
        f"Sun sets in {CITY} at {sunset_time} local time."
    ]
    return info_meteo

def publish_on_topic(user, city, chat_id, tmp, feel_tmp, hum, weather, wind, sub_period, notify_freq):
    bootstrap_servers = 'kafka:9092'  
    topic_name = 'example-topic'

    producer = KafkaProducer(
    bootstrap_servers=bootstrap_servers)

    # Messaggio da pubblicare sul topic
    message = user[0] + "," + city[0] + "," + str(chat_id[0]) + "," + str(tmp[0]) + "," + str(feel_tmp[0]) + "," + str(hum[0]) + "," + str(weather[0]) + "," + str(wind[0]) + "," + str(sub_period[0]) + "," + str(notify_freq)
    producer.send(topic_name, value=message.encode('utf-8'))

    time.sleep(1)   
    producer.close()



