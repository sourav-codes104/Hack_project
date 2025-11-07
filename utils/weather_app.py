import requests

def get_weather(location):
    try:
        api_key = "demo_key"  # Replace with real OpenWeatherMap key
        url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
        res = requests.get(url).json()
        return f"{res['weather'][0]['description'].title()}, {res['main']['temp']}°C"
    except:
        return "Weather data unavailable"
