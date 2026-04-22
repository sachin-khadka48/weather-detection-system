# Weather App (All-In-One Web Dashboard)

This project is now a full weather command dashboard with automatic location loading, exact local time, forecast analytics, air quality, and interactive map tools.

## Features

- Automatic weather loading for your current location (with browser permission)
- City-based weather search and quick city shortcuts
- Exact live local time and date for the selected location
- Sunrise, sunset, and daylight duration details
- Next 24-hour forecast (3-hour intervals)
- Air quality (AQI, PM2.5, PM10, NO2, O3, CO)
- Interactive OpenStreetMap map with city marker
- Recent searches and favorite city shortcuts
- Celsius and Fahrenheit toggle
- Smart weather tips based on conditions
- One-click actions: refresh, copy summary, save favorite
- Responsive modern UI for desktop and mobile
- Graceful error handling for invalid city/network/API issues

## Tech Stack

- Python
- Flask
- requests
- HTML, CSS, JavaScript
- OpenWeather Current Weather API
- OpenWeather Forecast API
- OpenWeather Air Pollution API
- OpenStreetMap + Leaflet

## Quick Start

1. Move into the app directory:

```bash
cd weather-app
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set your OpenWeather API key:

PowerShell:

```powershell
$env:OPENWEATHER_API_KEY="YOUR_API_KEY"
```

4. Start the web app:

```bash
python src/web_app.py
```

5. Open in your browser:

```text
http://127.0.0.1:5000
```

## Alternate Entrypoint

You can also run:

```bash
python src/ui/app_ui.py
```

## Notes

- If no API key is provided, the app shows a setup error message.
- You can customize host/port with `FLASK_HOST`, `PORT`, and `FLASK_DEBUG` environment variables.