import requests
from flask import Flask, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

API_KEY = "07ae890582be15d21bbe4f8fa989559c"
# API_KEY = "YOUR_API_KEY"  # 🔑 replace this

def get_weather(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    
    response = requests.get(url)
    data = response.json()

    if response.status_code != 200:
        return {"error": data.get("message", "Failed to fetch weather")}

    weather = {
        "location": {
            "name": data.get("name"),
            "country": data.get("sys", {}).get("country"),
            "coordinates": {
                "lat": data.get("coord", {}).get("lat"),
                "lon": data.get("coord", {}).get("lon")
            }
        },

        "temperature": {
            "current": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "min": data["main"]["temp_min"],
            "max": data["main"]["temp_max"]
        },

        "atmosphere": {
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "visibility": data.get("visibility", 0) / 1000  # km
        },

        "weather": {
            "main": data["weather"][0]["main"],
            "description": data["weather"][0]["description"],
            "icon": f"http://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png"
        },

        "wind": {
            "speed": data["wind"]["speed"],
            "direction": data["wind"].get("deg")
        },

        "clouds": {
            "coverage": data["clouds"]["all"]
        },

        "sun": {
            "sunrise": datetime.fromtimestamp(data["sys"]["sunrise"]).strftime('%H:%M:%S'),
            "sunset": datetime.fromtimestamp(data["sys"]["sunset"]).strftime('%H:%M:%S')
        },

        "timestamp": datetime.fromtimestamp(data["dt"]).strftime('%Y-%m-%d %H:%M:%S')
    }

    return weather


@app.route("/weather")
def weather():
    # Kolkata coordinates
    lat, lon = 22.5726, 88.3639
    
    data = get_weather(lat, lon)
    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True)