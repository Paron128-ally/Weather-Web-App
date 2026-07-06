import os
from datetime import datetime, timezone

import requests
from flask import Flask, jsonify, redirect, render_template, request, send_from_directory

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
app = Flask(__name__, static_folder=None, template_folder=BASE_DIR)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET,OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

BASE_URL = "https://api.openweathermap.org/data/2.5"
GEO_URL = "https://api.openweathermap.org/geo/1.0"
AIR_URL = "https://api.openweathermap.org/data/2.5/air_pollution"
UVI_URL = "https://api.openweathermap.org/data/2.5/uvi"


def get_api_key():
    return os.environ.get("OPENWEATHER_API_KEY", "your_api_key").strip()


@app.route("/")
@app.route("/index.html")
def index_html():
    return render_template("index.html")


@app.route("/images/<path:filename>")
def image_file(filename):
    return send_from_directory(IMAGES_DIR, filename)


@app.route("/static/<path:filename>")
def static_file(filename):
    return send_from_directory(os.path.join(BASE_DIR, "static"), filename)


@app.route("/static")
@app.route("/static/")
def static_root():
    return redirect("/", code=302)


@app.route("/<path:unused>")
def catch_all(unused):
    return redirect("/", code=302)


def fetch_json(url, *, params):
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


@app.route("/api/weather")
def get_weather():
    city = request.args.get("city", "Mumbai")
    api_key = get_api_key()

    if not api_key:
        return (
            jsonify(
                {
                    "error": "Missing OPENWEATHER_API_KEY. Add your OpenWeather API key before requesting weather data."
                }
            ),
            500,
        )

    try:
        geo_data = fetch_json(
            f"{GEO_URL}/direct",
            params={"q": city, "limit": 1, "appid": api_key},
        )
        if not geo_data:
            return jsonify({"error": f"City '{city}' not found."}), 404

        lat = geo_data[0]["lat"]
        lon = geo_data[0]["lon"]
        country = geo_data[0].get("country", "")
        state = geo_data[0].get("state", "")

        weather_data = fetch_json(
            f"{BASE_URL}/weather",
            params={"lat": lat, "lon": lon, "appid": api_key, "units": "metric"},
        )
        forecast_raw = fetch_json(
            f"{BASE_URL}/forecast",
            params={"lat": lat, "lon": lon, "appid": api_key, "units": "metric"},
        )
    except requests.HTTPError as error:
        status_code = error.response.status_code if error.response is not None else 502
        if status_code == 401:
            return (
                jsonify(
                    {
                        "error": "OpenWeather rejected the API key. Set OPENWEATHER_API_KEY to a valid key from your OpenWeather account."
                    }
                ),
                502,
            )
        return jsonify({"error": f"OpenWeather request failed with status {status_code}."}), 502
    except requests.RequestException:
        return jsonify({"error": "Unable to reach OpenWeather from the backend."}), 502

    try:
        aqi_data = fetch_json(
            AIR_URL,
            params={"lat": lat, "lon": lon, "appid": api_key},
        )
    except requests.RequestException:
        aqi_data = {}

    try:
        uvi_data = fetch_json(
            UVI_URL,
            params={"lat": lat, "lon": lon, "appid": api_key},
        )
    except requests.RequestException:
        uvi_data = {}

    aqi_index = aqi_data["list"][0]["main"]["aqi"] if aqi_data.get("list") else None
    aqi_labels = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}
    aqi_label = aqi_labels.get(aqi_index, "N/A")

    sunrise_ts = weather_data["sys"]["sunrise"]
    sunset_ts = weather_data["sys"]["sunset"]
    tz_offset = weather_data["timezone"]

    def fmt_local(timestamp):
        dt = datetime.fromtimestamp(timestamp + tz_offset, tz=timezone.utc)
        return dt.strftime("%I:%M %p")

    daily = {}
    for item in forecast_raw.get("list", []):
        date_str = item["dt_txt"].split(" ")[0]
        if date_str not in daily:
            daily[date_str] = {
                "date": date_str,
                "temp_min": item["main"]["temp_min"],
                "temp_max": item["main"]["temp_max"],
                "description": item["weather"][0]["description"],
                "icon": item["weather"][0]["icon"],
            }
        else:
            daily[date_str]["temp_min"] = min(
                daily[date_str]["temp_min"], item["main"]["temp_min"]
            )
            daily[date_str]["temp_max"] = max(
                daily[date_str]["temp_max"], item["main"]["temp_max"]
            )

    forecast_days = list(daily.values())[:5]
    uv_index = uvi_data.get("value")

    result = {
        "city": weather_data["name"],
        "country": country,
        "state": state,
        "temperature": round(weather_data["main"]["temp"]),
        "feels_like": round(weather_data["main"]["feels_like"]),
        "description": weather_data["weather"][0]["description"],
        "icon": weather_data["weather"][0]["icon"],
        "humidity": weather_data["main"]["humidity"],
        "wind_speed": round(weather_data["wind"]["speed"] * 3.6, 1),
        "visibility": round(weather_data.get("visibility", 0) / 1000, 1),
        "pressure": weather_data["main"]["pressure"],
        "sunrise": fmt_local(sunrise_ts),
        "sunset": fmt_local(sunset_ts),
        "uv_index": uv_index if uv_index is not None else "N/A",
        "aqi": f"{aqi_label} ({aqi_index})" if aqi_index else "N/A",
        "forecast": forecast_days,
    }
    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5500"))
    print(f"Starting Weather app on http://127.0.0.1:{port}/")
    app.run(debug=True, port=port)
