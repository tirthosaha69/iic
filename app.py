# import json
# import re
# import traceback
# import requests
# from datetime import datetime
# from flask import Flask, jsonify, render_template, request
# from langchain_groq import ChatGroq

# app = Flask(__name__)

# # ─────────────────────────────────────────────
# # API KEYS — replace OWM key with your own
# # Get free key at: openweathermap.org/api
# # ─────────────────────────────────────────────
# GROQ_API_KEY = "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"
# OWM_API_KEY  = "07ae890582be15d21bbe4f8fa989559c"   # <-- replace this

# # ─────────────────────────────────────────────
# # LLM — single instance
# # ─────────────────────────────────────────────
# _llm = ChatGroq(model="openai/gpt-oss-20b", api_key=GROQ_API_KEY)

# def call_llm(prompt: str) -> str:
#     response = _llm.invoke(prompt)
#     return response.content if hasattr(response, "content") else str(response)

# def parse_llm_json(raw: str) -> dict:
#     cleaned = re.sub(r'```(?:json)?\s*', '', raw).strip().replace('```', '').strip()
#     start = cleaned.find('{')
#     end   = cleaned.rfind('}')
#     if start == -1 or end == -1:
#         raise ValueError(f"No JSON found: {cleaned[:300]}")
#     return json.loads(cleaned[start:end + 1])

# def now_str():
#     return datetime.now().strftime("%Y-%m-%d %H:%M IST")


# # ═══════════════════════════════════════════════════════
# # OPENWEATHERMAP FETCHERS
# # ═══════════════════════════════════════════════════════

# # City → lat/lon map for West Bengal districts (OWM geocoding fallback)
# CITY_COORDS = {
#     "west bengal":     (22.9868,  87.8550),
#     "kolkata":         (22.5726,  88.3639),
#     "howrah":          (22.5958,  88.2636),
#     "darjeeling":      (27.0360,  88.2627),
#     "siliguri":        (26.7271,  88.3953),
#     "asansol":         (23.6889,  86.9661),
#     "durgapur":        (23.4800,  87.3200),
#     "bardhaman":       (23.2324,  87.8615),
#     "bankura":         (23.2324,  87.0753),
#     "purulia":         (23.3314,  86.3664),
#     "birbhum":         (23.9000,  87.5300),
#     "murshidabad":     (24.1800,  88.2700),
#     "nadia":           (23.4736,  88.5556),
#     "north 24 parganas":(22.7,   88.4),
#     "south 24 parganas":(22.1,   88.5),
#     "malda":           (25.0109,  88.1418),
#     "jalpaiguri":      (26.5449,  88.7179),
#     "cooch behar":     (26.3244,  89.4458),
#     "alipurduar":      (26.4900,  89.5300),
#     "midnapore":       (22.4255,  87.3195),
#     "hooghly":         (22.9000,  88.3900),
# }


# def get_coords(location: str) -> tuple[float, float]:
#     """Return (lat, lon) for a location string."""
#     key = location.lower().strip()
#     # Direct match
#     if key in CITY_COORDS:
#         return CITY_COORDS[key]
#     # Partial match
#     for city, coords in CITY_COORDS.items():
#         if city in key or key in city:
#             return coords
#     # OWM geocoding API
#     try:
#         url = f"http://api.openweathermap.org/geo/1.0/direct"
#         r = requests.get(url, params={"q": location + ",IN", "limit": 1, "appid": OWM_API_KEY}, timeout=5)
#         data = r.json()
#         if data:
#             return data[0]["lat"], data[0]["lon"]
#     except Exception as e:
#         print(f"[GEOCODE] error: {e}")
#     # Default: West Bengal centroid
#     return (22.9868, 87.8550)


# def fetch_current_weather(lat: float, lon: float) -> dict:
#     """Fetch current weather from OWM."""
#     try:
#         url = "https://api.openweathermap.org/data/2.5/weather"
#         r = requests.get(url, params={
#             "lat": lat, "lon": lon,
#             "appid": OWM_API_KEY,
#             "units": "metric"
#         }, timeout=8)
#         r.raise_for_status()
#         d = r.json()
#         return {
#             "temp":        round(d["main"]["temp"], 1),
#             "feels_like":  round(d["main"]["feels_like"], 1),
#             "humidity":    d["main"]["humidity"],
#             "pressure":    d["main"]["pressure"],
#             "wind_speed":  d["wind"]["speed"],
#             "description": d["weather"][0]["description"],
#             "visibility":  d.get("visibility", 0) // 1000,
#             "rain_1h":     d.get("rain", {}).get("1h", 0),
#             "rain_3h":     d.get("rain", {}).get("3h", 0),
#             "clouds":      d["clouds"]["all"],
#         }
#     except Exception as e:
#         print(f"[OWM CURRENT] error: {e}")
#         return {}


# def fetch_forecast(lat: float, lon: float) -> dict:
#     """Fetch 5-day / 3-hour forecast from OWM."""
#     try:
#         url = "https://api.openweathermap.org/data/2.5/forecast"
#         r = requests.get(url, params={
#             "lat": lat, "lon": lon,
#             "appid": OWM_API_KEY,
#             "units": "metric",
#             "cnt": 40   # 5 days × 8 per day
#         }, timeout=8)
#         r.raise_for_status()
#         d = r.json()
#         items = d.get("list", [])

#         # Aggregate daily rainfall totals (next 5 days)
#         daily_rain = {}
#         daily_temp = {}
#         for item in items:
#             day = item["dt_txt"][:10]
#             rain = item.get("rain", {}).get("3h", 0)
#             temp = item["main"]["temp"]
#             daily_rain[day] = daily_rain.get(day, 0) + rain
#             daily_temp.setdefault(day, []).append(temp)

#         days = sorted(daily_rain.keys())
#         total_5day_rain = sum(daily_rain.values())
#         avg_temps = {d: round(sum(t)/len(t), 1) for d, t in daily_temp.items()}

#         return {
#             "total_5day_rain_mm": round(total_5day_rain, 1),
#             "daily_rain":         {d: round(daily_rain[d], 1) for d in days},
#             "daily_avg_temp":     avg_temps,
#             "next_day_rain":      round(daily_rain.get(days[0], 0), 1) if days else 0,
#         }
#     except Exception as e:
#         print(f"[OWM FORECAST] error: {e}")
#         return {}


# def fetch_air_quality(lat: float, lon: float) -> dict:
#     """Fetch air quality index from OWM (proxy for pollution indicator)."""
#     try:
#         url = "https://api.openweathermap.org/data/2.5/air_pollution"
#         r = requests.get(url, params={
#             "lat": lat, "lon": lon,
#             "appid": OWM_API_KEY
#         }, timeout=8)
#         r.raise_for_status()
#         d = r.json()
#         comp = d["list"][0]["components"]
#         aqi  = d["list"][0]["main"]["aqi"]   # 1=Good, 2=Fair, 3=Moderate, 4=Poor, 5=Very Poor
#         return {
#             "aqi":    aqi,
#             "aqi_label": ["","Good","Fair","Moderate","Poor","Very Poor"][aqi],
#             "co":     comp.get("co", 0),
#             "no2":    comp.get("no2", 0),
#             "o3":     comp.get("o3", 0),
#             "pm2_5":  comp.get("pm2_5", 0),
#             "pm10":   comp.get("pm10", 0),
#             "so2":    comp.get("so2", 0),
#             "nh3":    comp.get("nh3", 0),
#         }
#     except Exception as e:
#         print(f"[OWM AQI] error: {e}")
#         return {}


# def build_weather_context(location: str) -> dict:
#     """Fetch all OWM data for a location and return combined dict."""
#     lat, lon = get_coords(location)
#     current  = fetch_current_weather(lat, lon)
#     forecast = fetch_forecast(lat, lon)
#     aqi      = fetch_air_quality(lat, lon)
#     return {
#         "location": location,
#         "lat": lat, "lon": lon,
#         "current": current,
#         "forecast": forecast,
#         "air_quality": aqi,
#     }


# # ═══════════════════════════════════════════════════════
# # ROUTES
# # ═══════════════════════════════════════════════════════

# @app.route('/')
# def index():
#     return render_template('index.html')


# # ── 1. Flood Risk / Main Dashboard ──
# @app.route('/api/water-data')
# def get_water_data():
#     location = request.args.get('location', 'West Bengal, India')
#     now = now_str()
#     wx  = build_weather_context(location)

#     prompt = f"""You are a hydrological risk analyst AI for {location}.
# Current time: {now}

# LIVE DATA FROM OPENWEATHERMAP:
# - Temperature:        {wx['current'].get('temp', 'N/A')} C
# - Feels Like:         {wx['current'].get('feels_like', 'N/A')} C
# - Humidity:           {wx['current'].get('humidity', 'N/A')}%
# - Pressure:           {wx['current'].get('pressure', 'N/A')} hPa
# - Wind Speed:         {wx['current'].get('wind_speed', 'N/A')} m/s
# - Rain last 1h:       {wx['current'].get('rain_1h', 0)} mm
# - Rain last 3h:       {wx['current'].get('rain_3h', 0)} mm
# - Cloud Cover:        {wx['current'].get('clouds', 'N/A')}%
# - Description:        {wx['current'].get('description', 'N/A')}
# - 5-Day Total Rain:   {wx['forecast'].get('total_5day_rain_mm', 'N/A')} mm
# - Daily Rain Forecast:{json.dumps(wx['forecast'].get('daily_rain', {}))}
# - Air Quality Index:  {wx['air_quality'].get('aqi_label', 'N/A')} (AQI={wx['air_quality'].get('aqi', 'N/A')})
# - PM2.5:              {wx['air_quality'].get('pm2_5', 'N/A')} ug/m3
# - SO2:                {wx['air_quality'].get('so2', 'N/A')} ug/m3
# - Coordinates:        {wx['lat']}, {wx['lon']}

# Using ONLY the live data above, generate a water crisis dashboard JSON for {location}.
# Apply these rules:
# - rain_1h > 20mm OR rain_3h > 50mm  → flood risk = HIGH
# - rain_1h 5-20mm OR rain_3h 15-50mm → flood risk = MODERATE
# - otherwise                          → flood risk = LOW
# - humidity > 85% and rain high       → stress = HIGH
# - AQI >= 4 (Poor/Very Poor)          → pollution = HIGH
# - AQI = 3 (Moderate)                 → pollution = MODERATE
# - AQI <= 2                           → pollution = LOW
# - 5-day total rain < 20mm            → drought risk increases
# - groundwater: estimate from humidity and rainfall (range -3 to -13m)
# - reservoir capacity: estimate from recent rainfall (range 20-95%)
# - discharge: estimate from rainfall intensity (range 150-1500 m3/s)
# - alerts: generate 3 specific real alerts based on actual values above

# Output ONLY valid JSON, no markdown, no extra text:
# {{
#   "location_info": {{
#     "temp": "{wx['current'].get('temp', '?')}C",
#     "rainfall": "{wx['current'].get('rain_3h', 0)} mm",
#     "discharge": "<estimate from rainfall data> m3/s",
#     "groundwater": "<estimate from humidity+rainfall> m",
#     "humidity": "{wx['current'].get('humidity', '?')}%"
#   }},
#   "risks": {{
#     "flood": "<LOW|MODERATE|HIGH using rainfall rule above>",
#     "stress": "<LOW|MODERATE|HIGH>",
#     "pollution": "<LOW|MODERATE|HIGH using AQI rule above>",
#     "drought": "<LOW|MODERATE|HIGH>"
#   }},
#   "reservoir": {{
#     "capacity_pct": <integer estimated from rainfall>,
#     "trend": "<trend based on forecast rain>",
#     "status": "<Normal|Below Normal|Critical|Above Normal>"
#   }},
#   "drought_monitor": {{
#     "risk_pct": <integer 0-100 based on 5-day rain and humidity>,
#     "soil_moisture": "<LOW|MODERATE|HIGH>",
#     "evapo": "<estimate mm/day based on temp and wind>",
#     "deficit": "<negative mm based on 5-day rain>"
#   }},
#   "water_quality": {{
#     "ph": "<estimate 6.4-8.5 based on rain intensity>",
#     "turbidity": "<estimate NTU, higher when rain_3h is high>",
#     "do": "<estimate mg/L, lower when temp is high>",
#     "conductivity": "<estimate uS/cm>"
#   }},
#   "alerts": [
#     "<specific alert using real temperature {wx['current'].get('temp','?')}C and rain {wx['current'].get('rain_3h',0)}mm>",
#     "<specific alert using real AQI {wx['air_quality'].get('aqi_label','?')} and SO2 {wx['air_quality'].get('so2','?')}>",
#     "<specific alert using 5-day forecast rain {wx['forecast'].get('total_5day_rain_mm','?')}mm>"
#   ]
# }}"""

#     try:
#         raw = call_llm(prompt)
#         print(f"[water-data] raw: {raw[:200]}")
#         data = parse_llm_json(raw)
#         return jsonify(data)
#     except Exception as e:
#         print(f"[water-data ERROR] {e}")
#         traceback.print_exc()
#         return jsonify({"error": str(e), "fallback": True}), 500


# # ── 2. Water Stress ──
# @app.route('/api/water-stress')
# def get_water_stress():
#     location = request.args.get('location', 'West Bengal, India')
#     now = now_str()
#     wx  = build_weather_context(location)

#     prompt = f"""You are a water stress analyst AI for {location}.
# Current time: {now}

# LIVE DATA FROM OPENWEATHERMAP:
# - Temperature:        {wx['current'].get('temp', 'N/A')} C
# - Humidity:           {wx['current'].get('humidity', 'N/A')}%
# - Wind Speed:         {wx['current'].get('wind_speed', 'N/A')} m/s
# - Rain last 3h:       {wx['current'].get('rain_3h', 0)} mm
# - 5-Day Total Rain:   {wx['forecast'].get('total_5day_rain_mm', 'N/A')} mm
# - Daily Rain:         {json.dumps(wx['forecast'].get('daily_rain', {}))}
# - Daily Avg Temp:     {json.dumps(wx['forecast'].get('daily_avg_temp', {}))}
# - Pressure:           {wx['current'].get('pressure', 'N/A')} hPa

# Using this LIVE data, generate realistic water stress analysis for {location}.
# High temp + low rain = high agricultural stress and drought risk.
# Low rainfall over 5 days = increasing water stress index.
# Generate real district names from {location} for hotspot_districts.
# Generate specific actionable recommendations for {location} based on the data.

# Output ONLY valid JSON, no markdown:
# {{
#   "overall_stress_index": <integer 0-100 derived from rainfall and temp data>,
#   "stress_level": "<LOW|MODERATE|HIGH>",
#   "demand_vs_supply": {{
#     "demand_mcm": <realistic integer for {location}>,
#     "supply_mcm": <integer less than demand when stressed>,
#     "deficit_pct": <calculated integer>
#   }},
#   "sector_stress": {{
#     "agricultural": "<LOW|MODERATE|HIGH based on rain and temp>",
#     "industrial": "<LOW|MODERATE|HIGH>",
#     "domestic": "<LOW|MODERATE|HIGH>",
#     "environmental_flow": "<LOW|MODERATE|HIGH>"
#   }},
#   "groundwater_depletion_rate": "<estimate m/year for {location}>",
#   "surface_water_availability": "<based on 5-day rain: Normal|Below Average|Well Below Average|Above Average>",
#   "inter_basin_transfer": "<Active|Inactive|Planned>",
#   "irrigation_efficiency": "<realistic percent for {location}>",
#   "per_capita_availability": "<realistic m3/year for {location}>",
#   "stress_forecast_30d": [<8 integers showing trend based on forecast data>],
#   "hotspot_districts": [<3-5 real districts most water-stressed in {location}>],
#   "recommendations": [
#     "<specific recommendation for {location} based on temp={wx['current'].get('temp','?')}C and rain={wx['current'].get('rain_3h',0)}mm>",
#     "<specific recommendation 2>",
#     "<specific recommendation 3>"
#   ],
#   "alerts": [
#     "<specific stress alert based on live data for {location}>",
#     "<specific groundwater or irrigation alert>"
#   ]
# }}"""

#     try:
#         raw = call_llm(prompt)
#         print(f"[water-stress] raw: {raw[:200]}")
#         data = parse_llm_json(raw)
#         return jsonify(data)
#     except Exception as e:
#         print(f"[water-stress ERROR] {e}")
#         traceback.print_exc()
#         return jsonify({"error": str(e), "fallback": True}), 500


# # ── 3. Pollution Alert ──
# @app.route('/api/pollution-alert')
# def get_pollution_alert():
#     location = request.args.get('location', 'West Bengal, India')
#     now = now_str()
#     wx  = build_weather_context(location)
#     aqi = wx.get('air_quality', {})

#     prompt = f"""You are a water and air pollution analyst AI for {location}.
# Current time: {now}

# LIVE DATA FROM OPENWEATHERMAP AIR QUALITY API:
# - AQI (1=Good to 5=VeryPoor): {aqi.get('aqi', 'N/A')} ({aqi.get('aqi_label', 'N/A')})
# - CO:    {aqi.get('co', 'N/A')} ug/m3
# - NO2:   {aqi.get('no2', 'N/A')} ug/m3
# - O3:    {aqi.get('o3', 'N/A')} ug/m3
# - PM2.5: {aqi.get('pm2_5', 'N/A')} ug/m3
# - PM10:  {aqi.get('pm10', 'N/A')} ug/m3
# - SO2:   {aqi.get('so2', 'N/A')} ug/m3
# - NH3:   {aqi.get('nh3', 'N/A')} ug/m3

# WEATHER CONTEXT:
# - Temperature:  {wx['current'].get('temp', 'N/A')} C
# - Humidity:     {wx['current'].get('humidity', 'N/A')}%
# - Wind Speed:   {wx['current'].get('wind_speed', 'N/A')} m/s
# - Rain last 3h: {wx['current'].get('rain_3h', 0)} mm

# Using the LIVE AQI data above, generate water pollution analysis for {location}.
# High AQI, NO2, SO2 indicate industrial pollution affecting water bodies.
# High NH3 indicates agricultural/sewage runoff.
# Generate realistic water pollutant estimates DERIVED from the AQI data.
# Use real industrial zones and river names in {location}.

# Output ONLY valid JSON, no markdown:
# {{
#   "overall_pollution_index": <integer 0-100 derived from AQI={aqi.get('aqi', 3)}>,
#   "alert_level": "<LOW|MODERATE|HIGH matching AQI level>",
#   "pollutants": {{
#     "arsenic_ppb": <estimate based on industrial activity and NH3={aqi.get('nh3', 0)}>,
#     "fluoride_mg_l": <estimate>,
#     "iron_mg_l": <estimate based on SO2={aqi.get('so2', 0)}>,
#     "nitrate_mg_l": <estimate based on NH3={aqi.get('nh3', 0)}>,
#     "coliform_cfu_ml": <estimate based on rainfall and NH3>,
#     "heavy_metals": "<LOW|MODERATE|HIGH based on AQI>"
#   }},
#   "river_quality": {{
#     "hooghly":    "<LOW|MODERATE|HIGH>",
#     "damodar":    "<LOW|MODERATE|HIGH>",
#     "teesta":     "<LOW|MODERATE|HIGH>",
#     "rupnarayan": "<LOW|MODERATE|HIGH>"
#   }},
#   "industrial_discharge_zones": [<real industrial zones in {location}>],
#   "safe_drinking_water_pct": <integer estimate for {location}>,
#   "wqi_score": <integer 0-100 derived from AQI and weather>,
#   "trend": "<Improving|Worsening|Stable>",
#   "critical_contaminant": "<most critical based on real AQI data above>",
#   "affected_population": "<realistic population estimate for {location}>",
#   "treatment_plants_operational": <integer>,
#   "treatment_plants_total": <integer>,
#   "alerts": [
#     "<specific alert using real AQI={aqi.get('aqi_label','?')} and PM2.5={aqi.get('pm2_5','?')}ug/m3>",
#     "<specific alert using real SO2={aqi.get('so2','?')} and NO2={aqi.get('no2','?')} levels>"
#   ]
# }}"""

#     try:
#         raw = call_llm(prompt)
#         print(f"[pollution-alert] raw: {raw[:200]}")
#         data = parse_llm_json(raw)
#         return jsonify(data)
#     except Exception as e:
#         print(f"[pollution-alert ERROR] {e}")
#         traceback.print_exc()
#         return jsonify({"error": str(e), "fallback": True}), 500


# # ── 4. Drought Forecast ──
# @app.route('/api/drought-forecast')
# def get_drought_forecast():
#     location = request.args.get('location', 'West Bengal, India')
#     now = now_str()
#     wx  = build_weather_context(location)

#     total_rain  = wx['forecast'].get('total_5day_rain_mm', 0)
#     rain_3h     = wx['current'].get('rain_3h', 0)
#     temp        = wx['current'].get('temp', 30)
#     humidity    = wx['current'].get('humidity', 70)
#     wind        = wx['current'].get('wind_speed', 2)

#     # Compute simple drought proxy from weather data
#     # Low rain + high temp + low humidity = drought conditions
#     drought_proxy = max(0, min(100, int(
#         (1 - min(total_rain, 100) / 100) * 50 +
#         max(0, temp - 25) * 2 +
#         max(0, 70 - humidity) * 0.5
#     )))

#     prompt = f"""You are a drought forecasting AI for {location}.
# Current time: {now}

# LIVE DATA FROM OPENWEATHERMAP:
# - Temperature:        {temp} C
# - Humidity:           {humidity}%
# - Wind Speed:         {wind} m/s
# - Rain last 3h:       {rain_3h} mm
# - 5-Day Total Rain:   {total_rain} mm
# - Daily Rain Forecast:{json.dumps(wx['forecast'].get('daily_rain', {}))}
# - Daily Avg Temp:     {json.dumps(wx['forecast'].get('daily_avg_temp', {}))}
# - Computed Drought Proxy Score: {drought_proxy}/100

# Using ONLY this LIVE data, generate a drought forecast for {location}.
# Calibrate all indices from the real weather readings above.
# - spi_3month: if total_rain < 30mm then negative (drought), else slightly positive
# - pdsi: correlate with temp and humidity
# - affected_area_pct: based on drought proxy score {drought_proxy}
# - soil_moisture: humidity < 60% = LOW, 60-80% = MODERATE, >80% = HIGH
# - crop_water_stress: high when temp > 33C and rain < 5mm
# - Use real district names from {location}

# Output ONLY valid JSON, no markdown:
# {{
#   "current_drought_index": {round(drought_proxy/100, 2)},
#   "spi_3month": <decimal derived from total_rain={total_rain}mm>,
#   "spi_6month": <decimal>,
#   "pdsi": <decimal derived from temp={temp}C and humidity={humidity}%>,
#   "drought_category": "<None|Abnormally Dry|Moderate Drought|Severe Drought|Extreme Drought>",
#   "affected_area_pct": <integer derived from drought proxy {drought_proxy}>,
#   "crop_water_stress": "<LOW|MODERATE|HIGH based on temp={temp}C and rain={rain_3h}mm>",
#   "pasture_condition": "<Good|Fair|Poor|Very Poor>",
#   "snowpack_anomaly": "N/A",
#   "streamflow_percentile": <integer derived from rainfall>,
#   "soil_moisture_anomaly": "<signed percent based on humidity={humidity}%>",
#   "forecast_90d": {{
#     "outlook": "<specific forecast for {location} based on daily rain forecast {json.dumps(wx['forecast'].get('daily_rain', {}))}>",
#     "probability_improvement": <integer based on forecast rain>,
#     "expected_rainfall_mm": {round(total_rain * 3.5, 1)},
#     "temperature_anomaly": "<signed decimal based on temp={temp}C vs 28C normal>C"
#   }},
#   "affected_districts": [<3-5 real districts in {location} most affected by drought>],
#   "crop_loss_estimate": "<range derived from drought proxy {drought_proxy}>",
#   "water_table_depth": "<negative decimal estimated from humidity={humidity}% and rain={total_rain}mm> m",
#   "livestock_impact": "<LOW|MODERATE|HIGH>",
#   "alerts": [
#     "<specific drought alert using real temp={temp}C and 5-day rain={total_rain}mm for {location}>",
#     "<specific soil or crop alert based on humidity={humidity}% and wind={wind}m/s>"
#   ]
# }}"""

#     try:
#         raw = call_llm(prompt)
#         print(f"[drought-forecast] raw: {raw[:200]}")
#         data = parse_llm_json(raw)
#         return jsonify(data)
#     except Exception as e:
#         print(f"[drought-forecast ERROR] {e}")
#         traceback.print_exc()
#         return jsonify({"error": str(e), "fallback": True}), 500


# # ── 5. Location Search ──
# @app.route('/api/search-location')
# def search_location():
#     query = request.args.get('q', '').strip()
#     if not query:
#         return jsonify({"error": "No query provided"}), 400
#     now = now_str()

#     # Try to fetch weather for searched location
#     wx = build_weather_context(query)
#     lat, lon = wx['lat'], wx['lon']

#     prompt = f"""You are a hydrological risk AI for location search.
# Current time: {now}
# User searched for: "{query}"

# LIVE OPENWEATHERMAP DATA FOR THIS LOCATION:
# - Coordinates:        {lat}, {lon}
# - Temperature:        {wx['current'].get('temp', 'N/A')} C
# - Humidity:           {wx['current'].get('humidity', 'N/A')}%
# - Rain last 3h:       {wx['current'].get('rain_3h', 0)} mm
# - Wind Speed:         {wx['current'].get('wind_speed', 'N/A')} m/s
# - Description:        {wx['current'].get('description', 'N/A')}
# - 5-Day Total Rain:   {wx['forecast'].get('total_5day_rain_mm', 'N/A')} mm
# - AQI:                {wx['air_quality'].get('aqi_label', 'N/A')}
# - PM2.5:              {wx['air_quality'].get('pm2_5', 'N/A')} ug/m3

# If "{query}" is NOT a real location in or near India, return {{"found": false}}.
# Otherwise use the LIVE data above to fill this JSON.
# Derive all risk levels directly from the live weather and AQI values.

# Output ONLY valid JSON, no markdown:
# {{
#   "found": true,
#   "location_name": "<official name of {query}>",
#   "coordinates": {{"lat": {lat}, "lng": {lon}}},
#   "district": "<district containing {query}>",
#   "state": "<state>",
#   "summary": "<2 specific sentences about current water/weather situation for {query} based on the live data above>",
#   "location_info": {{
#     "temp": "{wx['current'].get('temp', '?')}C",
#     "rainfall": "{wx['current'].get('rain_3h', 0)} mm",
#     "discharge": "<estimate m3/s from rain data>",
#     "groundwater": "<estimate from humidity and rain> m",
#     "humidity": "{wx['current'].get('humidity', '?')}%"
#   }},
#   "risks": {{
#     "flood": "<LOW|MODERATE|HIGH from rain_3h={wx['current'].get('rain_3h',0)}mm>",
#     "stress": "<LOW|MODERATE|HIGH>",
#     "pollution": "<LOW|MODERATE|HIGH from AQI={wx['air_quality'].get('aqi','?')}>",
#     "drought": "<LOW|MODERATE|HIGH>"
#   }},
#   "reservoir": {{"capacity_pct": <estimate from rain>, "trend": "<trend>", "status": "<status>"}},
#   "drought_monitor": {{"risk_pct": <estimate>, "soil_moisture": "<LOW|MODERATE|HIGH>", "evapo": "<estimate> mm/day", "deficit": "<negative mm>"}},
#   "water_quality": {{"ph": "<estimate>", "turbidity": "<estimate> NTU", "do": "<estimate> mg/L", "conductivity": "<estimate> uS/cm"}},
#   "key_water_bodies": [<real rivers and lakes near {query}>],
#   "historical_events": [<1-2 real notable water events in {query}>],
#   "alerts": [
#     "<specific real alert for {query} using live temp={wx['current'].get('temp','?')}C and rain={wx['current'].get('rain_3h',0)}mm>",
#     "<specific alert from AQI={wx['air_quality'].get('aqi_label','?')} data>"
#   ]
# }}"""

#     try:
#         raw = call_llm(prompt)
#         print(f"[search] raw: {raw[:200]}")
#         data = parse_llm_json(raw)
#         return jsonify(data)
#     except Exception as e:
#         print(f"[search ERROR] {e}")
#         traceback.print_exc()
#         return jsonify({"found": False, "error": str(e)}), 500


# if __name__ == '__main__':
#     app.run(debug=True, port=5000)

import json
import re
import traceback
import requests
from datetime import datetime
from flask import Flask, jsonify, render_template, request
from langchain_groq import ChatGroq

app = Flask(__name__)

# ─────────────────────────────────────────────
# API KEYS — replace OWM key with your own
# Get free key at: openweathermap.org/api
# ─────────────────────────────────────────────
GROQ_API_KEY = "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"
OWM_API_KEY  = "07ae890582be15d21bbe4f8fa989559c"   # <-- replace this

# ─────────────────────────────────────────────
# LLM — single instance
# ─────────────────────────────────────────────
_llm = ChatGroq(model="openai/gpt-oss-20b", api_key=GROQ_API_KEY)

def call_llm(prompt: str) -> str:
    response = _llm.invoke(prompt)
    return response.content if hasattr(response, "content") else str(response)

def parse_llm_json(raw: str) -> dict:
    cleaned = re.sub(r'```(?:json)?\s*', '', raw).strip().replace('```', '').strip()
    start = cleaned.find('{')
    end   = cleaned.rfind('}')
    if start == -1 or end == -1:
        raise ValueError(f"No JSON found: {cleaned[:300]}")
    return json.loads(cleaned[start:end + 1])

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M IST")


# ═══════════════════════════════════════════════════════
# OPENWEATHERMAP FETCHERS
# ═══════════════════════════════════════════════════════

# City → lat/lon map for West Bengal districts (OWM geocoding fallback)
CITY_COORDS = {
    "west bengal":     (22.9868,  87.8550),
    "kolkata":         (22.5726,  88.3639),
    "howrah":          (22.5958,  88.2636),
    "darjeeling":      (27.0360,  88.2627),
    "siliguri":        (26.7271,  88.3953),
    "asansol":         (23.6889,  86.9661),
    "durgapur":        (23.4800,  87.3200),
    "bardhaman":       (23.2324,  87.8615),
    "bankura":         (23.2324,  87.0753),
    "purulia":         (23.3314,  86.3664),
    "birbhum":         (23.9000,  87.5300),
    "murshidabad":     (24.1800,  88.2700),
    "nadia":           (23.4736,  88.5556),
    "north 24 parganas":(22.7,   88.4),
    "south 24 parganas":(22.1,   88.5),
    "malda":           (25.0109,  88.1418),
    "jalpaiguri":      (26.5449,  88.7179),
    "cooch behar":     (26.3244,  89.4458),
    "alipurduar":      (26.4900,  89.5300),
    "midnapore":       (22.4255,  87.3195),
    "hooghly":         (22.9000,  88.3900),
}


def get_coords(location: str) -> tuple[float, float]:
    """Return (lat, lon) for a location string."""
    key = location.lower().strip()
    # Direct match
    if key in CITY_COORDS:
        return CITY_COORDS[key]
    # Partial match
    for city, coords in CITY_COORDS.items():
        if city in key or key in city:
            return coords
    # OWM geocoding API
    try:
        url = f"http://api.openweathermap.org/geo/1.0/direct"
        r = requests.get(url, params={"q": location + ",IN", "limit": 1, "appid": OWM_API_KEY}, timeout=5)
        data = r.json()
        if data:
            return data[0]["lat"], data[0]["lon"]
    except Exception as e:
        print(f"[GEOCODE] error: {e}")
    # Default: West Bengal centroid
    return (22.9868, 87.8550)


def fetch_current_weather(lat: float, lon: float) -> dict:
    """Fetch current weather from OWM."""
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        r = requests.get(url, params={
            "lat": lat, "lon": lon,
            "appid": OWM_API_KEY,
            "units": "metric"
        }, timeout=8)
        r.raise_for_status()
        d = r.json()
        return {
            "temp":        round(d["main"]["temp"], 1),
            "feels_like":  round(d["main"]["feels_like"], 1),
            "humidity":    d["main"]["humidity"],
            "pressure":    d["main"]["pressure"],
            "wind_speed":  d["wind"]["speed"],
            "description": d["weather"][0]["description"],
            "visibility":  d.get("visibility", 0) // 1000,
            "rain_1h":     d.get("rain", {}).get("1h", 0),
            "rain_3h":     d.get("rain", {}).get("3h", 0),
            "clouds":      d["clouds"]["all"],
        }
    except Exception as e:
        print(f"[OWM CURRENT] error: {e}")
        return {}


def fetch_forecast(lat: float, lon: float) -> dict:
    """Fetch 5-day / 3-hour forecast from OWM."""
    try:
        url = "https://api.openweathermap.org/data/2.5/forecast"
        r = requests.get(url, params={
            "lat": lat, "lon": lon,
            "appid": OWM_API_KEY,
            "units": "metric",
            "cnt": 40   # 5 days × 8 per day
        }, timeout=8)
        r.raise_for_status()
        d = r.json()
        items = d.get("list", [])

        # Aggregate daily rainfall totals (next 5 days)
        daily_rain = {}
        daily_temp = {}
        for item in items:
            day = item["dt_txt"][:10]
            rain = item.get("rain", {}).get("3h", 0)
            temp = item["main"]["temp"]
            daily_rain[day] = daily_rain.get(day, 0) + rain
            daily_temp.setdefault(day, []).append(temp)

        days = sorted(daily_rain.keys())
        total_5day_rain = sum(daily_rain.values())
        avg_temps = {d: round(sum(t)/len(t), 1) for d, t in daily_temp.items()}

        return {
            "total_5day_rain_mm": round(total_5day_rain, 1),
            "daily_rain":         {d: round(daily_rain[d], 1) for d in days},
            "daily_avg_temp":     avg_temps,
            "next_day_rain":      round(daily_rain.get(days[0], 0), 1) if days else 0,
        }
    except Exception as e:
        print(f"[OWM FORECAST] error: {e}")
        return {}


def fetch_air_quality(lat: float, lon: float) -> dict:
    """Fetch air quality index from OWM (proxy for pollution indicator)."""
    try:
        url = "https://api.openweathermap.org/data/2.5/air_pollution"
        r = requests.get(url, params={
            "lat": lat, "lon": lon,
            "appid": OWM_API_KEY
        }, timeout=8)
        r.raise_for_status()
        d = r.json()
        comp = d["list"][0]["components"]
        aqi  = d["list"][0]["main"]["aqi"]   # 1=Good, 2=Fair, 3=Moderate, 4=Poor, 5=Very Poor
        return {
            "aqi":    aqi,
            "aqi_label": ["","Good","Fair","Moderate","Poor","Very Poor"][aqi],
            "co":     comp.get("co", 0),
            "no2":    comp.get("no2", 0),
            "o3":     comp.get("o3", 0),
            "pm2_5":  comp.get("pm2_5", 0),
            "pm10":   comp.get("pm10", 0),
            "so2":    comp.get("so2", 0),
            "nh3":    comp.get("nh3", 0),
        }
    except Exception as e:
        print(f"[OWM AQI] error: {e}")
        return {}


def build_weather_context(location: str) -> dict:
    """Fetch all OWM data for a location and return combined dict."""
    lat, lon = get_coords(location)
    current  = fetch_current_weather(lat, lon)
    forecast = fetch_forecast(lat, lon)
    aqi      = fetch_air_quality(lat, lon)
    return {
        "location": location,
        "lat": lat, "lon": lon,
        "current": current,
        "forecast": forecast,
        "air_quality": aqi,
    }


# ═══════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('index.html')


# ── 1. Flood Risk / Main Dashboard ──
@app.route('/api/water-data')
def get_water_data():
    location = request.args.get('location', 'West Bengal, India')
    now = now_str()
    wx  = build_weather_context(location)

    prompt = f"""You are a hydrological risk analyst AI for {location}.
Current time: {now}

LIVE DATA FROM OPENWEATHERMAP:
- Temperature:        {wx['current'].get('temp', 'N/A')} C
- Feels Like:         {wx['current'].get('feels_like', 'N/A')} C
- Humidity:           {wx['current'].get('humidity', 'N/A')}%
- Pressure:           {wx['current'].get('pressure', 'N/A')} hPa
- Wind Speed:         {wx['current'].get('wind_speed', 'N/A')} m/s
- Rain last 1h:       {wx['current'].get('rain_1h', 0)} mm
- Rain last 3h:       {wx['current'].get('rain_3h', 0)} mm
- Cloud Cover:        {wx['current'].get('clouds', 'N/A')}%
- Description:        {wx['current'].get('description', 'N/A')}
- 5-Day Total Rain:   {wx['forecast'].get('total_5day_rain_mm', 'N/A')} mm
- Daily Rain Forecast:{json.dumps(wx['forecast'].get('daily_rain', {}))}
- Air Quality Index:  {wx['air_quality'].get('aqi_label', 'N/A')} (AQI={wx['air_quality'].get('aqi', 'N/A')})
- PM2.5:              {wx['air_quality'].get('pm2_5', 'N/A')} ug/m3
- SO2:                {wx['air_quality'].get('so2', 'N/A')} ug/m3
- Coordinates:        {wx['lat']}, {wx['lon']}

Using ONLY the live data above, generate a water crisis dashboard JSON for {location}.
Apply these rules:
- rain_1h > 20mm OR rain_3h > 50mm  → flood risk = HIGH
- rain_1h 5-20mm OR rain_3h 15-50mm → flood risk = MODERATE
- otherwise                          → flood risk = LOW
- humidity > 85% and rain high       → stress = HIGH
- AQI >= 4 (Poor/Very Poor)          → pollution = HIGH
- AQI = 3 (Moderate)                 → pollution = MODERATE
- AQI <= 2                           → pollution = LOW
- 5-day total rain < 20mm            → drought risk increases
- groundwater: estimate from humidity and rainfall (range -3 to -13m)
- reservoir capacity: estimate from recent rainfall (range 20-95%)
- discharge: estimate from rainfall intensity (range 150-1500 m3/s)
- alerts: generate 3 specific real alerts based on actual values above

Output ONLY valid JSON, no markdown, no extra text:
{{
  "location_info": {{
    "temp": "{wx['current'].get('temp', '?')}C",
    "rainfall": "{wx['current'].get('rain_3h', 0)} mm",
    "discharge": "<estimate from rainfall data> m3/s",
    "groundwater": "<estimate from humidity+rainfall> m",
    "humidity": "{wx['current'].get('humidity', '?')}%"
  }},
  "risks": {{
    "flood": "<LOW|MODERATE|HIGH using rainfall rule above>",
    "stress": "<LOW|MODERATE|HIGH>",
    "pollution": "<LOW|MODERATE|HIGH using AQI rule above>",
    "drought": "<LOW|MODERATE|HIGH>"
  }},
  "reservoir": {{
    "capacity_pct": <integer estimated from rainfall>,
    "trend": "<trend based on forecast rain>",
    "status": "<Normal|Below Normal|Critical|Above Normal>"
  }},
  "drought_monitor": {{
    "risk_pct": <integer 0-100 based on 5-day rain and humidity>,
    "soil_moisture": "<LOW|MODERATE|HIGH>",
    "evapo": "<estimate mm/day based on temp and wind>",
    "deficit": "<negative mm based on 5-day rain>"
  }},
  "water_quality": {{
    "ph": "<estimate 6.4-8.5 based on rain intensity>",
    "turbidity": "<estimate NTU, higher when rain_3h is high>",
    "do": "<estimate mg/L, lower when temp is high>",
    "conductivity": "<estimate uS/cm>"
  }},
  "alerts": [
    "<specific alert using real temperature {wx['current'].get('temp','?')}C and rain {wx['current'].get('rain_3h',0)}mm>",
    "<specific alert using real AQI {wx['air_quality'].get('aqi_label','?')} and SO2 {wx['air_quality'].get('so2','?')}>",
    "<specific alert using 5-day forecast rain {wx['forecast'].get('total_5day_rain_mm','?')}mm>"
  ]
}}"""

    try:
        raw = call_llm(prompt)
        print(f"[water-data] raw: {raw[:200]}")
        data = parse_llm_json(raw)
        return jsonify(data)
    except Exception as e:
        print(f"[water-data ERROR] {e}")
        traceback.print_exc()
        return jsonify({"error": str(e), "fallback": True}), 500


# ── 2. Water Stress ──
@app.route('/api/water-stress')
def get_water_stress():
    location = request.args.get('location', 'West Bengal, India')
    now = now_str()
    wx  = build_weather_context(location)

    prompt = f"""You are a water stress analyst AI for {location}.
Current time: {now}

LIVE DATA FROM OPENWEATHERMAP:
- Temperature:        {wx['current'].get('temp', 'N/A')} C
- Humidity:           {wx['current'].get('humidity', 'N/A')}%
- Wind Speed:         {wx['current'].get('wind_speed', 'N/A')} m/s
- Rain last 3h:       {wx['current'].get('rain_3h', 0)} mm
- 5-Day Total Rain:   {wx['forecast'].get('total_5day_rain_mm', 'N/A')} mm
- Daily Rain:         {json.dumps(wx['forecast'].get('daily_rain', {}))}
- Daily Avg Temp:     {json.dumps(wx['forecast'].get('daily_avg_temp', {}))}
- Pressure:           {wx['current'].get('pressure', 'N/A')} hPa

Using this LIVE data, generate realistic water stress analysis for {location}.
High temp + low rain = high agricultural stress and drought risk.
Low rainfall over 5 days = increasing water stress index.
Generate real district names from {location} for hotspot_districts.
Generate specific actionable recommendations for {location} based on the data.

Output ONLY valid JSON, no markdown:
{{
  "overall_stress_index": <integer 0-100 derived from rainfall and temp data>,
  "stress_level": "<LOW|MODERATE|HIGH>",
  "demand_vs_supply": {{
    "demand_mcm": <realistic integer for {location}>,
    "supply_mcm": <integer less than demand when stressed>,
    "deficit_pct": <calculated integer>
  }},
  "sector_stress": {{
    "agricultural": "<LOW|MODERATE|HIGH based on rain and temp>",
    "industrial": "<LOW|MODERATE|HIGH>",
    "domestic": "<LOW|MODERATE|HIGH>",
    "environmental_flow": "<LOW|MODERATE|HIGH>"
  }},
  "groundwater_depletion_rate": "<estimate m/year for {location}>",
  "surface_water_availability": "<based on 5-day rain: Normal|Below Average|Well Below Average|Above Average>",
  "inter_basin_transfer": "<Active|Inactive|Planned>",
  "irrigation_efficiency": "<realistic percent for {location}>",
  "per_capita_availability": "<realistic m3/year for {location}>",
  "stress_forecast_30d": [<8 integers showing trend based on forecast data>],
  "hotspot_districts": [<3-5 real districts most water-stressed in {location}>],
  "recommendations": [
    "<specific recommendation for {location} based on temp={wx['current'].get('temp','?')}C and rain={wx['current'].get('rain_3h',0)}mm>",
    "<specific recommendation 2>",
    "<specific recommendation 3>"
  ],
  "alerts": [
    "<specific stress alert based on live data for {location}>",
    "<specific groundwater or irrigation alert>"
  ]
}}"""

    try:
        raw = call_llm(prompt)
        print(f"[water-stress] raw: {raw[:200]}")
        data = parse_llm_json(raw)
        return jsonify(data)
    except Exception as e:
        print(f"[water-stress ERROR] {e}")
        traceback.print_exc()
        return jsonify({"error": str(e), "fallback": True}), 500


# ── 3. Pollution Alert ──
@app.route('/api/pollution-alert')
def get_pollution_alert():
    location = request.args.get('location', 'West Bengal, India')
    now = now_str()
    wx  = build_weather_context(location)
    aqi = wx.get('air_quality', {})

    prompt = f"""You are a water and air pollution analyst AI for {location}.
Current time: {now}

LIVE DATA FROM OPENWEATHERMAP AIR QUALITY API:
- AQI (1=Good to 5=VeryPoor): {aqi.get('aqi', 'N/A')} ({aqi.get('aqi_label', 'N/A')})
- CO:    {aqi.get('co', 'N/A')} ug/m3
- NO2:   {aqi.get('no2', 'N/A')} ug/m3
- O3:    {aqi.get('o3', 'N/A')} ug/m3
- PM2.5: {aqi.get('pm2_5', 'N/A')} ug/m3
- PM10:  {aqi.get('pm10', 'N/A')} ug/m3
- SO2:   {aqi.get('so2', 'N/A')} ug/m3
- NH3:   {aqi.get('nh3', 'N/A')} ug/m3

WEATHER CONTEXT:
- Temperature:  {wx['current'].get('temp', 'N/A')} C
- Humidity:     {wx['current'].get('humidity', 'N/A')}%
- Wind Speed:   {wx['current'].get('wind_speed', 'N/A')} m/s
- Rain last 3h: {wx['current'].get('rain_3h', 0)} mm

Using the LIVE AQI data above, generate water pollution analysis for {location}.
High AQI, NO2, SO2 indicate industrial pollution affecting water bodies.
High NH3 indicates agricultural/sewage runoff.
Generate realistic water pollutant estimates DERIVED from the AQI data.
Use real industrial zones and river names in {location}.

Output ONLY valid JSON, no markdown:
{{
  "overall_pollution_index": <integer 0-100 derived from AQI={aqi.get('aqi', 3)}>,
  "alert_level": "<LOW|MODERATE|HIGH matching AQI level>",
  "pollutants": {{
    "arsenic_ppb": <estimate based on industrial activity and NH3={aqi.get('nh3', 0)}>,
    "fluoride_mg_l": <estimate>,
    "iron_mg_l": <estimate based on SO2={aqi.get('so2', 0)}>,
    "nitrate_mg_l": <estimate based on NH3={aqi.get('nh3', 0)}>,
    "coliform_cfu_ml": <estimate based on rainfall and NH3>,
    "heavy_metals": "<LOW|MODERATE|HIGH based on AQI>"
  }},
  "river_quality": {{
    "hooghly":    "<LOW|MODERATE|HIGH>",
    "damodar":    "<LOW|MODERATE|HIGH>",
    "teesta":     "<LOW|MODERATE|HIGH>",
    "rupnarayan": "<LOW|MODERATE|HIGH>"
  }},
  "industrial_discharge_zones": [<real industrial zones in {location}>],
  "safe_drinking_water_pct": <integer estimate for {location}>,
  "wqi_score": <integer 0-100 derived from AQI and weather>,
  "trend": "<Improving|Worsening|Stable>",
  "critical_contaminant": "<most critical based on real AQI data above>",
  "affected_population": "<realistic population estimate for {location}>",
  "treatment_plants_operational": <integer>,
  "treatment_plants_total": <integer>,
  "alerts": [
    "<specific alert using real AQI={aqi.get('aqi_label','?')} and PM2.5={aqi.get('pm2_5','?')}ug/m3>",
    "<specific alert using real SO2={aqi.get('so2','?')} and NO2={aqi.get('no2','?')} levels>"
  ]
}}"""

    try:
        raw = call_llm(prompt)
        print(f"[pollution-alert] raw: {raw[:200]}")
        data = parse_llm_json(raw)
        return jsonify(data)
    except Exception as e:
        print(f"[pollution-alert ERROR] {e}")
        traceback.print_exc()
        return jsonify({"error": str(e), "fallback": True}), 500


# ── 4. Drought Forecast ──
@app.route('/api/drought-forecast')
def get_drought_forecast():
    location = request.args.get('location', 'West Bengal, India')
    now = now_str()
    wx  = build_weather_context(location)

    total_rain  = wx['forecast'].get('total_5day_rain_mm', 0)
    rain_3h     = wx['current'].get('rain_3h', 0)
    temp        = wx['current'].get('temp', 30)
    humidity    = wx['current'].get('humidity', 70)
    wind        = wx['current'].get('wind_speed', 2)

    # Compute simple drought proxy from weather data
    # Low rain + high temp + low humidity = drought conditions
    drought_proxy = max(0, min(100, int(
        (1 - min(total_rain, 100) / 100) * 50 +
        max(0, temp - 25) * 2 +
        max(0, 70 - humidity) * 0.5
    )))

    prompt = f"""You are a drought forecasting AI for {location}.
Current time: {now}

LIVE DATA FROM OPENWEATHERMAP:
- Temperature:        {temp} C
- Humidity:           {humidity}%
- Wind Speed:         {wind} m/s
- Rain last 3h:       {rain_3h} mm
- 5-Day Total Rain:   {total_rain} mm
- Daily Rain Forecast:{json.dumps(wx['forecast'].get('daily_rain', {}))}
- Daily Avg Temp:     {json.dumps(wx['forecast'].get('daily_avg_temp', {}))}
- Computed Drought Proxy Score: {drought_proxy}/100

Using ONLY this LIVE data, generate a drought forecast for {location}.
Calibrate all indices from the real weather readings above.
- spi_3month: if total_rain < 30mm then negative (drought), else slightly positive
- pdsi: correlate with temp and humidity
- affected_area_pct: based on drought proxy score {drought_proxy}
- soil_moisture: humidity < 60% = LOW, 60-80% = MODERATE, >80% = HIGH
- crop_water_stress: high when temp > 33C and rain < 5mm
- Use real district names from {location}

Output ONLY valid JSON, no markdown:
{{
  "current_drought_index": {round(drought_proxy/100, 2)},
  "spi_3month": <decimal derived from total_rain={total_rain}mm>,
  "spi_6month": <decimal>,
  "pdsi": <decimal derived from temp={temp}C and humidity={humidity}%>,
  "drought_category": "<None|Abnormally Dry|Moderate Drought|Severe Drought|Extreme Drought>",
  "affected_area_pct": <integer derived from drought proxy {drought_proxy}>,
  "crop_water_stress": "<LOW|MODERATE|HIGH based on temp={temp}C and rain={rain_3h}mm>",
  "pasture_condition": "<Good|Fair|Poor|Very Poor>",
  "snowpack_anomaly": "N/A",
  "streamflow_percentile": <integer derived from rainfall>,
  "soil_moisture_anomaly": "<signed percent based on humidity={humidity}%>",
  "forecast_90d": {{
    "outlook": "<specific forecast for {location} based on daily rain forecast {json.dumps(wx['forecast'].get('daily_rain', {}))}>",
    "probability_improvement": <integer based on forecast rain>,
    "expected_rainfall_mm": {round(total_rain * 3.5, 1)},
    "temperature_anomaly": "<signed decimal based on temp={temp}C vs 28C normal>C"
  }},
  "affected_districts": [<3-5 real districts in {location} most affected by drought>],
  "crop_loss_estimate": "<range derived from drought proxy {drought_proxy}>",
  "water_table_depth": "<negative decimal estimated from humidity={humidity}% and rain={total_rain}mm> m",
  "livestock_impact": "<LOW|MODERATE|HIGH>",
  "alerts": [
    "<specific drought alert using real temp={temp}C and 5-day rain={total_rain}mm for {location}>",
    "<specific soil or crop alert based on humidity={humidity}% and wind={wind}m/s>"
  ]
}}"""

    try:
        raw = call_llm(prompt)
        print(f"[drought-forecast] raw: {raw[:200]}")
        data = parse_llm_json(raw)
        return jsonify(data)
    except Exception as e:
        print(f"[drought-forecast ERROR] {e}")
        traceback.print_exc()
        return jsonify({"error": str(e), "fallback": True}), 500


# ── 5. Location Search ──
@app.route('/api/search-location')
def search_location():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"error": "No query provided"}), 400
    now = now_str()

    # Try to fetch weather for searched location
    wx = build_weather_context(query)
    lat, lon = wx['lat'], wx['lon']

    prompt = f"""You are a hydrological risk AI for location search.
Current time: {now}
User searched for: "{query}"

LIVE OPENWEATHERMAP DATA FOR THIS LOCATION:
- Coordinates:        {lat}, {lon}
- Temperature:        {wx['current'].get('temp', 'N/A')} C
- Humidity:           {wx['current'].get('humidity', 'N/A')}%
- Rain last 3h:       {wx['current'].get('rain_3h', 0)} mm
- Wind Speed:         {wx['current'].get('wind_speed', 'N/A')} m/s
- Description:        {wx['current'].get('description', 'N/A')}
- 5-Day Total Rain:   {wx['forecast'].get('total_5day_rain_mm', 'N/A')} mm
- AQI:                {wx['air_quality'].get('aqi_label', 'N/A')}
- PM2.5:              {wx['air_quality'].get('pm2_5', 'N/A')} ug/m3

If "{query}" is NOT a real location in or near India, return {{"found": false}}.
Otherwise use the LIVE data above to fill this JSON.
Derive all risk levels directly from the live weather and AQI values.

Output ONLY valid JSON, no markdown:
{{
  "found": true,
  "location_name": "<official name of {query}>",
  "coordinates": {{"lat": {lat}, "lng": {lon}}},
  "district": "<district containing {query}>",
  "state": "<state>",
  "summary": "<2 specific sentences about current water/weather situation for {query} based on the live data above>",
  "location_info": {{
    "temp": "{wx['current'].get('temp', '?')}C",
    "rainfall": "{wx['current'].get('rain_3h', 0)} mm",
    "discharge": "<estimate m3/s from rain data>",
    "groundwater": "<estimate from humidity and rain> m",
    "humidity": "{wx['current'].get('humidity', '?')}%"
  }},
  "risks": {{
    "flood": "<LOW|MODERATE|HIGH from rain_3h={wx['current'].get('rain_3h',0)}mm>",
    "stress": "<LOW|MODERATE|HIGH>",
    "pollution": "<LOW|MODERATE|HIGH from AQI={wx['air_quality'].get('aqi','?')}>",
    "drought": "<LOW|MODERATE|HIGH>"
  }},
  "reservoir": {{"capacity_pct": <estimate from rain>, "trend": "<trend>", "status": "<status>"}},
  "drought_monitor": {{"risk_pct": <estimate>, "soil_moisture": "<LOW|MODERATE|HIGH>", "evapo": "<estimate> mm/day", "deficit": "<negative mm>"}},
  "water_quality": {{"ph": "<estimate>", "turbidity": "<estimate> NTU", "do": "<estimate> mg/L", "conductivity": "<estimate> uS/cm"}},
  "key_water_bodies": [<real rivers and lakes near {query}>],
  "historical_events": [<1-2 real notable water events in {query}>],
  "alerts": [
    "<specific real alert for {query} using live temp={wx['current'].get('temp','?')}C and rain={wx['current'].get('rain_3h',0)}mm>",
    "<specific alert from AQI={wx['air_quality'].get('aqi_label','?')} data>"
  ]
}}"""

    try:
        raw = call_llm(prompt)
        print(f"[search] raw: {raw[:200]}")
        data = parse_llm_json(raw)
        return jsonify(data)
    except Exception as e:
        print(f"[search ERROR] {e}")
        traceback.print_exc()
        return jsonify({"found": False, "error": str(e)}), 500


# ── 6. AI Chat Assistant ──
@app.route('/api/chat')
def chat():
    q = request.args.get('q', '').strip()
    location = request.args.get('location', 'West Bengal, India')
    if not q:
        return jsonify({"error": "No question"}), 400

    prompt = (
        "You are an expert water crisis AI assistant for " + location + ".\n"
        "Answer the user's question concisely in 2-3 sentences using your knowledge of hydrology, "
        "water management, and current conditions in West Bengal, India.\n"
        "Be specific, factual, and actionable. No markdown.\n\n"
        "User question: " + q
    )
    try:
        raw = call_llm(prompt)
        return jsonify({"answer": raw.strip()})
    except Exception as e:
        print(f"[chat ERROR] {e}")
        return jsonify({"answer": "AI assistant unavailable. Please try again."}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)