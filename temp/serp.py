import requests

url = "https://www.searchapi.io/api/v1/search"
params = {
    "engine": "google",
    "q": "how many areas are affected in west bengal in last 24 hours weather changes",
    "api_key": "ymDYGGpxG4YpgNrBdWxZd3vB"
}

response = requests.get(url, params=params)
data = response.json()

for r in data.get("organic_results", []):
    print(r["title"], r["link"])