import requests

class WeatherAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"

    def fetch_weather(self, city):
        params = {
            'q': city,
            'appid': self.api_key,
            'units': 'metric'
        }
        try:
            response = requests.get(self.base_url, params=params)
            print("DEBUG:", response.status_code, response.text)  # Add this line
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except requests.RequestException:
            return None