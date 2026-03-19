import requests

url = "https://www.searchapi.io/api/v1/search"
params = {
    "engine": "google",
    "q": "weather today in kolkata",
    "api_key": "ymDYGGpxG4YpgNrBdWxZd3vB"
}

response = requests.get(url, params=params)
data = response.json()

for r in data.get("organic_results", []):
    print(r["title"], r["link"])