from kafka import KafkaProducer
import time, json, os
from random import choice

import datetime as dt
import requests

def return_weather(city):
    
    # Innanzitutto specifichiamo l'URL di base a cui inviamo le richieste
    BASE_URL = "http://api.openweathermap.org/data/2.5/weather?"
    # quindi l'api key che recupero dal txt
    #API_KEY = open('apiKey.txt','r').read()
    
    
    # Leggi la chiave API dal file specificato dalla variabile di ambiente
    # openweathermap_api_key_file = os.environ.get("OPENWEATHERMAP_API_KEY_FILE", "apiKey2.txt")
    # with open(openweathermap_api_key_file, 'r') as api_key_file:
        # API_KEY = api_key_file.read()
    API_KEY = os.environ.get("OPENWEATHERMAP_API_KEY_FILE", "NO_VARIABLE_FOUND")
    # e la città di cui vogliamo ottenere i dati
    CITY = city

    url = BASE_URL + "appid=" + API_KEY + "&q=" + CITY
    # facciamo una richiesta
    response = requests.get(url).json()

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

    humidity = response['main']['humidity']

    info_meteo = [
        f"Temperature in {CITY}: {temp_celsius:.2f}°C or {temp_fahr:.2f}°F",
        f"Temperature in {CITY} feels_like: {fl_celsius:.2f}°C or {fl_fahr:.2f}°F",
        f"Humidity in {CITY}: {humidity}%",
        f"Wind speed in {CITY}: {wind_speed}m/s",
        f"Sun rises in {CITY} at {sunrise_time} local time."
    ]
    return info_meteo

def publish_on_topic(user, city):
    bootstrap_servers = 'kafka:9092'  
    topic_name = 'example-topic'

    producer = KafkaProducer(
    bootstrap_servers=bootstrap_servers)

    message = str(user) + "," + str(city)
    #for i in message:

        # message = f"Message {i}"
        #message = i
    print(f"Message: {message}")
    producer.send(topic_name, value=message.encode('utf-8'))
    print(f"Produced: {message}")
    time.sleep(1)
        
    producer.close()