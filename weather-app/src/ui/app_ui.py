from flask import Flask, render_template, request
from utils.weather_api import WeatherAPI

app = Flask(__name__)
api_key = 'ecd53c9e8423f9e8b0cded3d83852b72'
weather_api = WeatherAPI(api_key)

@app.route('/', methods=['GET', 'POST'])
def index():
    weather = None
    error = None
    if request.method == 'POST':
        city = request.form.get('city')
        if city:
            data = weather_api.fetch_weather(city)
            if data and data.get('cod') == 200:
                weather = {
                    'city': data.get('name'),
                    'temperature': data['main']['temp'],
                    'humidity': data['main']['humidity'],
                    'condition': data['weather'][0]['description'],
                    'wind': data['wind']['speed']
                }
            else:
                error = "Could not retrieve weather data. Please check the city name."
        else:
            error = "Please enter a city name."
    return render_template('index.html', weather=weather, error=error)

if __name__ == '__main__':
    app.run(debug=True)