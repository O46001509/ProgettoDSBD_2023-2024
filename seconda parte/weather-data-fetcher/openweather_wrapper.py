import requests

# Classe che incapsula le chiamate all'API di OpenWeatherMap 
# per semplificare il recupero delle informazioni meteorologiche.
class OpenWeatherWrapper:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5/weather?"

    def get_weather_data(self, city_name):
        
        url = self.base_url + "lang=it" + "&appid=" + self.api_key + "&q=" + city_name
        response = requests.get(url)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Errore nella richiesta API: {response.status_code}")
            return None








