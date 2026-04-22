import requests

class WeatherAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        self.forecast_url = "https://api.openweathermap.org/data/2.5/forecast"
        self.air_quality_url = "https://api.openweathermap.org/data/2.5/air_pollution"

    def _request_json(self, url, params, include_units=False):
        if not self.api_key:
            return {'cod': 'missing_api_key', 'message': 'Missing API key for weather service.'}

        final_params = {**params, 'appid': self.api_key}
        if include_units:
            final_params['units'] = 'metric'

        try:
            response = requests.get(url, params=final_params, timeout=10)
            try:
                return response.json()
            except ValueError:
                return {'cod': 'invalid_response', 'message': 'Weather service returned an invalid response.'}
        except requests.RequestException:
            return {'cod': 'network_error', 'message': 'Network error while contacting weather service.'}

    def _request_weather(self, params):
        return self._request_json(self.base_url, params, include_units=True)

    def fetch_weather(self, city):
        return self._request_weather({'q': city})

    def fetch_weather_by_coords(self, latitude, longitude):
        return self._request_weather({'lat': latitude, 'lon': longitude})

    def fetch_forecast(self, city=None, latitude=None, longitude=None):
        params = {}
        if city:
            params['q'] = city
        elif latitude is not None and longitude is not None:
            params['lat'] = latitude
            params['lon'] = longitude
        else:
            return {'cod': 'invalid_input', 'message': 'Missing city or coordinates for forecast lookup.'}

        return self._request_json(self.forecast_url, params, include_units=True)

    def fetch_air_quality(self, latitude, longitude):
        return self._request_json(self.air_quality_url, {'lat': latitude, 'lon': longitude})