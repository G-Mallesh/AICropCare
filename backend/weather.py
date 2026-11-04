import requests


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def get_weather(location):

    location = location.strip()

    if not location:
        raise ValueError("Please enter a city or village name.")

    # Find location coordinates
    geo_response = requests.get(
        GEOCODING_URL,
        params={
            "name": location,
            "count": 1,
            "language": "en",
            "format": "json"
        },
        timeout=15
    )

    geo_response.raise_for_status()
    geo_data = geo_response.json()

    locations = geo_data.get("results", [])

    if not locations:
        raise ValueError("Location not found. Check the spelling.")

    place = locations[0]

    latitude = place["latitude"]
    longitude = place["longitude"]

    # Get current weather and today's forecast
    weather_response = requests.get(
        WEATHER_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "precipitation,"
                "weather_code,"
                "wind_speed_10m"
            ),
            "daily": (
                "precipitation_sum,"
                "precipitation_probability_max,"
                "temperature_2m_max,"
                "temperature_2m_min"
            ),
            "timezone": "auto",
            "forecast_days": 1
        },
        timeout=15
    )

    weather_response.raise_for_status()
    data = weather_response.json()

    current = data.get("current", {})
    daily = data.get("daily", {})

    return {
        "location": place["name"],
        "state": place.get("admin1", ""),
        "country": place.get("country", ""),
        "temperature": current.get("temperature_2m"),
        "humidity": current.get("relative_humidity_2m"),
        "precipitation": current.get("precipitation"),
        "weather_code": current.get("weather_code"),
        "wind_speed": current.get("wind_speed_10m"),
        "rainfall_today": (
            daily.get("precipitation_sum", [None])[0]
        ),
        "rain_probability": (
            daily.get("precipitation_probability_max", [None])[0]
        ),
        "max_temperature": (
            daily.get("temperature_2m_max", [None])[0]
        ),
        "min_temperature": (
            daily.get("temperature_2m_min", [None])[0]
        ),
        "time": current.get("time")
    }


def get_farming_advice(weather):

    advice = []

    temperature = weather.get("temperature")
    humidity = weather.get("humidity")
    rainfall = weather.get("rainfall_today")
    rain_probability = weather.get("rain_probability")

    if temperature is not None and temperature >= 35:
        advice.append(
            "High temperature: monitor crops for heat stress "
            "and irrigate according to soil moisture and crop needs."
        )

    if humidity is not None and humidity >= 80:
        advice.append(
            "High humidity: monitor crops for fungal diseases "
            "and maintain suitable field ventilation."
        )

    if rainfall is not None and rainfall >= 10:
        advice.append(
            "Rain is forecast: check field drainage and avoid "
            "unnecessary irrigation."
        )

    if rain_probability is not None and rain_probability >= 60:
        advice.append(
            "Rain is likely: check the local forecast before "
            "spraying or applying fertilizer."
        )

    if not advice:
        advice.append(
            "Continue regular crop monitoring. Check soil moisture "
            "before irrigation and follow local agricultural advice."
        )

    return advice