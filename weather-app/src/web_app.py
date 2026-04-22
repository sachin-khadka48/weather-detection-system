from datetime import datetime, timedelta, timezone
import os

from flask import Flask, jsonify, render_template, request
from utils.weather_api import WeatherAPI

app = Flask(__name__)
default_api_key = 'ecd53c9e8423f9e8b0cded3d83852b72'
api_key = os.getenv('OPENWEATHER_API_KEY', default_api_key).strip()
weather_api = WeatherAPI(api_key)


def _weather_icon(condition):
    normalized = condition.lower()
    if 'thunder' in normalized:
        return '⛈'
    if 'rain' in normalized or 'drizzle' in normalized:
        return '🌧'
    if 'snow' in normalized:
        return '❄'
    if 'mist' in normalized or 'fog' in normalized or 'haze' in normalized:
        return '🌫'
    if 'cloud' in normalized:
        return '☁'
    return '☀'


def _format_metric(value, unit='', decimals=1):
    if isinstance(value, (int, float)):
        if decimals == 0:
            return f'{value:.0f}{unit}'
        return f'{value:.{decimals}f}{unit}'
    return 'N/A'


def _to_local_datetime(epoch_seconds, offset_seconds):
    if not isinstance(epoch_seconds, (int, float)):
        return None

    offset = int(offset_seconds) if isinstance(offset_seconds, (int, float)) else 0
    utc_dt = datetime.fromtimestamp(epoch_seconds, tz=timezone.utc)
    return utc_dt + timedelta(seconds=offset)


def _format_local_time(epoch_seconds, offset_seconds, fmt):
    local_dt = _to_local_datetime(epoch_seconds, offset_seconds)
    if not local_dt:
        return 'N/A'
    return local_dt.strftime(fmt)


def _format_utc_offset(offset_seconds):
    if not isinstance(offset_seconds, (int, float)):
        return 'UTC'

    offset = int(offset_seconds)
    sign = '+' if offset >= 0 else '-'
    total = abs(offset)
    hours = total // 3600
    minutes = (total % 3600) // 60
    return f'UTC{sign}{hours:02d}:{minutes:02d}'


def _aqi_label(aqi):
    mapping = {
        1: 'Good',
        2: 'Fair',
        3: 'Moderate',
        4: 'Poor',
        5: 'Very Poor'
    }
    return mapping.get(aqi, 'Unknown')


def _build_air_quality_payload(data):
    if not isinstance(data, dict):
        return None

    rows = data.get('list', [])
    if not rows or not isinstance(rows[0], dict):
        return None

    item = rows[0]
    aqi_value = item.get('main', {}).get('aqi')
    components = item.get('components', {})

    return {
        'aqi': aqi_value,
        'label': _aqi_label(aqi_value),
        'pm2_5': _format_metric(components.get('pm2_5'), ' μg/m³', 1),
        'pm10': _format_metric(components.get('pm10'), ' μg/m³', 1),
        'no2': _format_metric(components.get('no2'), ' μg/m³', 1),
        'o3': _format_metric(components.get('o3'), ' μg/m³', 1),
        'co': _format_metric(components.get('co'), ' μg/m³', 1)
    }


def _build_forecast_payload(data, fallback_offset=0):
    if not isinstance(data, dict):
        return []

    city = data.get('city', {})
    timezone_offset = city.get('timezone', fallback_offset)

    entries = []
    for item in data.get('list', []):
        if not isinstance(item, dict):
            continue
        if len(entries) >= 8:
            break

        main = item.get('main', {})
        weather_info = item.get('weather', [{}])[0]
        temp_c = main.get('temp')
        rain_chance = item.get('pop')

        rain_pct = 'N/A'
        if isinstance(rain_chance, (int, float)):
            rain_pct = f"{int(round(rain_chance * 100))}%"

        entries.append({
            'day': _format_local_time(item.get('dt'), timezone_offset, '%a'),
            'time': _format_local_time(item.get('dt'), timezone_offset, '%I:%M %p'),
            'icon': _weather_icon(weather_info.get('main', weather_info.get('description', ''))),
            'temp': _format_metric(temp_c, '°C', 1),
            'temp_c': temp_c,
            'condition': weather_info.get('description', 'Unknown').title(),
            'rain_chance': rain_pct
        })

    return entries


def _build_weather_tips(weather, air_quality=None):
    tips = []
    temp_c = weather.get('temperature_c')
    humidity = weather.get('humidity_value')
    wind = weather.get('wind_value')
    condition = weather.get('condition', '').lower()

    if isinstance(temp_c, (int, float)) and temp_c >= 33:
        tips.append('High heat detected. Hydrate often and avoid direct sun during peak afternoon hours.')
    if isinstance(temp_c, (int, float)) and temp_c <= 6:
        tips.append('Low temperature outside. Wear layers and keep your evening commute warm.')
    if isinstance(humidity, (int, float)) and humidity >= 80:
        tips.append('Humidity is high. Keep ventilation on to stay comfortable indoors.')
    if isinstance(wind, (int, float)) and wind >= 10:
        tips.append('Winds are strong. Secure loose outdoor items and watch travel conditions.')
    if 'rain' in condition or 'drizzle' in condition:
        tips.append('Rain is likely. Keep an umbrella handy before stepping out.')

    if air_quality and isinstance(air_quality.get('aqi'), int) and air_quality['aqi'] >= 4:
        tips.append('Air quality is low. Limit intense outdoor activity and use a mask if sensitive.')

    if not tips:
        tips.append('Conditions look stable. Great time for outdoor plans and a short walk.')

    return tips[:4]


def _build_weather_payload(data, fallback_city=''):
    main = data.get('main', {})
    weather_info = data.get('weather', [{}])[0]
    wind = data.get('wind', {})
    visibility = data.get('visibility')
    coord = data.get('coord', {})
    system = data.get('sys', {})
    clouds = data.get('clouds', {})

    timezone_offset = data.get('timezone', 0)
    observed_at = data.get('dt')
    sunrise_ts = system.get('sunrise')
    sunset_ts = system.get('sunset')

    visibility_km = None
    if isinstance(visibility, (int, float)):
        visibility_km = visibility / 1000

    latitude = coord.get('lat')
    longitude = coord.get('lon')
    cloud_pct = clouds.get('all')
    condition = weather_info.get('description', 'Unknown').title()

    local_epoch = None
    if isinstance(observed_at, (int, float)):
        offset_value = int(timezone_offset) if isinstance(timezone_offset, (int, float)) else 0
        local_epoch = int(observed_at + offset_value)

    is_daytime = None
    daylight_hours = None
    if isinstance(observed_at, (int, float)) and isinstance(sunrise_ts, (int, float)) and isinstance(sunset_ts, (int, float)):
        is_daytime = sunrise_ts <= observed_at <= sunset_ts
        daylight_hours = (sunset_ts - sunrise_ts) / 3600

    city_name = data.get('name', fallback_city.title() if fallback_city else 'Unknown')
    temp_str = _format_metric(main.get('temp'), '°C', 1)
    feels_like_str = _format_metric(main.get('feels_like'), '°C', 1)

    return {
        'city': city_name,
        'country': system.get('country', ''),
        'temperature': temp_str,
        'temperature_c': main.get('temp'),
        'temp_min': _format_metric(main.get('temp_min'), '°C', 1),
        'temp_min_c': main.get('temp_min'),
        'temp_max': _format_metric(main.get('temp_max'), '°C', 1),
        'temp_max_c': main.get('temp_max'),
        'humidity': _format_metric(main.get('humidity'), '%', 0),
        'humidity_value': main.get('humidity'),
        'condition': condition,
        'wind': _format_metric(wind.get('speed'), ' m/s', 1),
        'wind_value': wind.get('speed'),
        'feels_like': feels_like_str,
        'feels_like_c': main.get('feels_like'),
        'pressure': _format_metric(main.get('pressure'), ' hPa', 0),
        'pressure_value': main.get('pressure'),
        'cloud_cover': _format_metric(cloud_pct, '%', 0),
        'cloud_cover_value': cloud_pct,
        'visibility': _format_metric(visibility_km, ' km', 1),
        'visibility_km': visibility_km,
        'icon': _weather_icon(weather_info.get('main', weather_info.get('description', ''))),
        'updated_at_local': _format_local_time(observed_at, timezone_offset, '%b %d, %I:%M %p'),
        'local_time': _format_local_time(observed_at, timezone_offset, '%I:%M:%S %p'),
        'local_date': _format_local_time(observed_at, timezone_offset, '%A, %b %d %Y'),
        'timezone_label': _format_utc_offset(timezone_offset),
        'utc_offset_seconds': int(timezone_offset) if isinstance(timezone_offset, (int, float)) else 0,
        'local_epoch': local_epoch,
        'sunrise_local': _format_local_time(sunrise_ts, timezone_offset, '%I:%M %p'),
        'sunset_local': _format_local_time(sunset_ts, timezone_offset, '%I:%M %p'),
        'daylight_hours': _format_metric(daylight_hours, ' h', 1),
        'is_daytime': is_daytime,
        'lat': latitude,
        'lon': longitude,
        'summary': f'{condition} in {city_name}. Temperature {temp_str}, feels like {feels_like_str}.',
        'map_link': (
            f'https://www.openstreetmap.org/?mlat={float(latitude):.5f}&mlon={float(longitude):.5f}#map=11/{float(latitude):.5f}/{float(longitude):.5f}'
            if isinstance(latitude, (int, float)) and isinstance(longitude, (int, float))
            else None
        )
    }


def _extract_error_message(data):
    if isinstance(data, dict):
        message = data.get('message')
        if isinstance(message, str) and message.strip():
            return message.strip().capitalize()
    return ''


def _load_extras(mode, city_query, weather):
    forecast = []
    air_quality = None

    lat = weather.get('lat')
    lon = weather.get('lon')

    if mode == 'coords' and isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
        forecast_data = weather_api.fetch_forecast(latitude=lat, longitude=lon)
    else:
        forecast_data = weather_api.fetch_forecast(city=city_query or weather.get('city'))

    if forecast_data and str(forecast_data.get('cod')) == '200':
        forecast = _build_forecast_payload(forecast_data, fallback_offset=weather.get('utc_offset_seconds', 0))

    if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
        aqi_data = weather_api.fetch_air_quality(lat, lon)
        air_quality = _build_air_quality_payload(aqi_data)

    return forecast, air_quality


@app.route('/', methods=['GET', 'POST'])
def index():
    weather = None
    forecast = []
    air_quality = None
    tips = []
    error = None

    city_query = ''
    last_mode = 'city'
    last_lat = ''
    last_lon = ''

    if request.method == 'POST':
        mode = request.form.get('mode', 'city').strip().lower()
        city_query = request.form.get('city', '').strip()
        last_mode = mode if mode in ('city', 'coords') else 'city'

        if not api_key:
            error = 'API key is missing. Set OPENWEATHER_API_KEY and try again.'
        else:
            data = None

            if last_mode == 'coords':
                lat_raw = request.form.get('lat', '').strip()
                lon_raw = request.form.get('lon', '').strip()
                last_lat = lat_raw
                last_lon = lon_raw

                try:
                    latitude = float(lat_raw)
                    longitude = float(lon_raw)
                    data = weather_api.fetch_weather_by_coords(latitude, longitude)
                except ValueError:
                    error = 'Could not read your location coordinates. Please try typing your city.'
            else:
                if not city_query:
                    error = 'Please enter a city name.'
                else:
                    data = weather_api.fetch_weather(city_query)

            if not error and data and str(data.get('cod')) == '200':
                weather = _build_weather_payload(data, fallback_city=city_query)
                if last_mode == 'coords':
                    city_query = weather.get('city', city_query)

                forecast, air_quality = _load_extras(last_mode, city_query, weather)
                tips = _build_weather_tips(weather, air_quality)
            elif not error:
                api_message = _extract_error_message(data)
                error = 'Could not retrieve weather data. Please check the city name.'
                if last_mode == 'coords':
                    error = 'Could not retrieve weather data for your current location.'
                if api_message:
                    error = f'{error} {api_message}'

    return render_template(
        'Index.html',
        weather=weather,
        forecast=forecast,
        air_quality=air_quality,
        tips=tips,
        error=error,
        city_query=city_query,
        last_mode=last_mode,
        last_lat=last_lat,
        last_lon=last_lon
    )


@app.route('/api/weather-by-location', methods=['POST'])
def weather_by_location():
    if not api_key:
        return jsonify({'ok': False, 'error': 'API key is missing. Set OPENWEATHER_API_KEY and try again.'}), 400

    payload = request.get_json(silent=True) or {}
    try:
        latitude = float(payload.get('lat'))
        longitude = float(payload.get('lon'))
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'error': 'Invalid coordinates from browser location service.'}), 400

    data = weather_api.fetch_weather_by_coords(latitude, longitude)
    if data and str(data.get('cod')) == '200':
        weather = _build_weather_payload(data)
        forecast, air_quality = _load_extras('coords', weather.get('city', ''), weather)
        tips = _build_weather_tips(weather, air_quality)
        return jsonify({'ok': True, 'weather': weather, 'forecast': forecast, 'air_quality': air_quality, 'tips': tips})

    error_message = _extract_error_message(data) or 'Failed to fetch weather for this location.'
    return jsonify({'ok': False, 'error': error_message}), 502


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'service': 'weather-dashboard'})


def _read_port():
    try:
        return int(os.getenv('PORT', '5000'))
    except ValueError:
        return 5000


if __name__ == '__main__':
    app.run(
        debug=os.getenv('FLASK_DEBUG', '1') == '1',
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=_read_port()
    )