import datetime as dt
import requests
import os


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
        f"Wind speed in {CITY}: {wind_speed*3.6}km/h",
        f"Sun rises in {CITY} at {sunrise_time} local time.",
        f"Sun sets in {CITY} at {sunset_time} local time."
    ]
    return info_meteo

def select_constraint_from_info_weather(info_meteo, city_constraints):
    info_meteo_costraint = []
    if city_constraints[0] == True:
        info_meteo_costraint.append(info_meteo[0])
    if city_constraints[1] == True:
        info_meteo_costraint.append(info_meteo[1])
    if city_constraints[2] == True:
        info_meteo_costraint.append(info_meteo[2])
    if city_constraints[3] == True:
        info_meteo_costraint.append(info_meteo[3])
    if city_constraints[4] == True:
        info_meteo_costraint.append(info_meteo[4])
    return info_meteo_costraint