# Mausam — Weather App

A simple Flask + vanilla JS weather app that shows current conditions and a 5-day forecast using the OpenWeatherMap API.

## Setup

1. Clone the repo and enter the folder:
   ```bash
   git clone <your-repo-url>
   cd Weather
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # on Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Get a free API key from [OpenWeatherMap](https://openweathermap.org/api) and add it to a `.env` file:
   ```bash
   cp .env.example .env
   # then edit .env and paste your key in
   ```

4. Run the app:
   ```bash
   python app.py
   ```

5. Open http://127.0.0.1:5000 in your browser.

## Tech
- Flask backend (`static/wtf.py`)
- Vanilla JS frontend (`static/wow.js`)
- OpenWeatherMap API (current weather, forecast, air quality, UV index)
