from utils.weather_api import WeatherAPI

def display_weather_info(weather_data):
    if weather_data:
        city = weather_data.get('name', 'Unknown')
        main = weather_data.get('main', {})
        weather = weather_data.get('weather', [{}])[0]
        wind = weather_data.get('wind', {})

        temperature = main.get('temp', 'N/A')
        humidity = main.get('humidity', 'N/A')
        weather_condition = weather.get('description', 'N/A')      
        wind_speed = wind.get('speed', 'N/A')

        print(f"\nWeather in {city}:")
        print(f"Temperature: {temperature}°C")
        print(f"Humidity: {humidity}%")
        print(f"Condition: {weather_condition.capitalize()}")
        print(f"Wind Speed: {wind_speed} m/s\n")
    else:
        print("Could not retrieve weather data. Please check the city name.\n")

def main():
    api_key = 'ecd53c9e8423f9e8b0cded3d83852b72'  
    weather_api = WeatherAPI(api_key)
    while True:
        city = input("Enter city name (or type 'exit' to quit): ")
        if city.lower() == 'exit':
            print("Goodbye!")
            break
        weather_data = weather_api.fetch_weather(city)
        display_weather_info(weather_data)

if __name__ == "__main__":
    main()