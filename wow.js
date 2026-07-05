const cityInput = document.getElementById('city-input');
const errorMsg = document.getElementById('error-message');
const mainContent = document.getElementById('main-content');
const loader = document.getElementById('loader');
const LOCAL_API_BASE = 'http://127.0.0.1:5500';

function normalizeApiBase(base) {
    return base.replace(/\/+$/, '');
}

function getApiBases() {
    const configuredBase = window.WEATHER_API_BASE || document.body?.dataset.apiBase;
    if (configuredBase) {
        return [normalizeApiBase(configuredBase)];
    }

    if (window.location.protocol === 'file:') {
        return [LOCAL_API_BASE];
    }

    const bases = [normalizeApiBase(window.location.origin)];
    const isLocalPage = ['127.0.0.1', 'localhost'].includes(window.location.hostname);

    if (isLocalPage && bases[0] !== LOCAL_API_BASE) {
        bases.push(LOCAL_API_BASE);
    }

    return [...new Set(bases)];
}

const API_BASES = getApiBases();

const imageUrls = [
    './images/day-cloudy.jpg',
    './images/day-rainy.jpg',
    './images/day-snowy.jpg',
    './images/day-sunny.jpg',
    './images/night-cloudy.jpg',
    './images/night-rainy.jpg',
    './images/night-snowy.jpg',
    './images/night-sunny.jpg',
];

const DEFAULT_CITY = 'Mumbai';

function setRandomBackground() {
    const randomIndex = Math.floor(Math.random() * imageUrls.length);
    const selectedImageUrl = imageUrls[randomIndex];
    document.body.style.backgroundImage = `url("${selectedImageUrl}")`;
}

setRandomBackground();
cityInput.value = DEFAULT_CITY;

function showError(message) {
    errorMsg.textContent = message;
    errorMsg.classList.add('visible');
    setTimeout(() => errorMsg.classList.remove('visible'), 4000);
}

function clearError() {
    errorMsg.textContent = '';
    errorMsg.classList.remove('visible');
}

function showLoader() {
    loader.classList.remove('hidden');
}

function hideLoader() {
    loader.classList.add('hidden');
}

function formatDate(dateStr) {
    const date = new Date(`${dateStr}T00:00:00`);
    return date.toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
    });
}

function renderForecast(forecast) {
    const container = document.getElementById('forecast-cards');
    container.innerHTML = '';

    forecast.forEach((day) => {
        const card = document.createElement('div');
        card.className = 'forecast-card';
        card.innerHTML = `
            <span class="fc-day">${formatDate(day.date)}</span>
            <img src="https://openweathermap.org/img/wn/${day.icon}@2x.png" alt="${day.description}">
            <span class="fc-desc">${day.description}</span>
            <span class="fc-temps">
                <span class="hi">${Math.round(day.temp_max)}\u00B0</span>
                <span class="lo">${Math.round(day.temp_min)}\u00B0</span>
            </span>
        `;
        container.appendChild(card);
    });
}

async function getWeather(cityOverride) {
    const city = cityOverride || cityInput.value.trim();
    if (!city) {
        showError('Please enter a city name.');
        return;
    }

    setRandomBackground();
    clearError();
    showLoader();

    try {
        const data = await fetchWeather(city);

        const locationLabel = data.state
            ? `${data.city}, ${data.state}, ${data.country}`
            : `${data.city}, ${data.country}`;

        document.getElementById('city-name').textContent = locationLabel;
        document.getElementById('temperature').textContent = `${data.temperature}\u00B0C`;
        document.getElementById('description').textContent = data.description;
        document.getElementById('feels-like-value').textContent = `${data.feels_like}\u00B0C`;
        document.getElementById('visibility-value').textContent = `${data.visibility} km`;
        document.getElementById('sunrise-value').textContent = data.sunrise;
        document.getElementById('sunset-inline').textContent = data.sunset;
        document.getElementById('humidity-value').textContent = `${data.humidity}%`;
        document.getElementById('wind-speed-value').textContent = `${data.wind_speed} km/h`;
        document.getElementById('uv-value').textContent = data.uv_index;
        document.getElementById('pressure-value').textContent = `${data.pressure} hPa`;
        document.getElementById('aqi-value').textContent = data.aqi;

        const iconEl = document.getElementById('weather-icon');
        iconEl.src = `https://openweathermap.org/img/wn/${data.icon}@4x.png`;
        iconEl.alt = data.description;

        renderForecast(data.forecast);
        mainContent.classList.add('revealed');
    } catch (error) {
        console.error(error);
        showError(error instanceof Error ? error.message : 'Network error. Please try again.');
    } finally {
        hideLoader();
    }
}

async function fetchWeather(city) {
    let lastError = new Error('Unable to reach the weather service.');

    for (const apiBase of API_BASES) {
        try {
            const response = await fetch(`${apiBase}/api/weather?city=${encodeURIComponent(city)}`);
            const contentType = response.headers.get('content-type') || '';
            const isJson = contentType.includes('application/json');
            const data = isJson ? await response.json() : null;

            if (response.ok && data) {
                return data;
            }

            lastError = new Error(
                data?.error || `Weather request failed with status ${response.status}.`
            );

            if (response.status !== 404 && isJson) {
                throw lastError;
            }
        } catch (error) {
            lastError = error instanceof Error
                ? error
                : new Error('Unable to reach the weather service.');
        }
    }

    throw lastError;
}

cityInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        getWeather();
    }
});

window.addEventListener('DOMContentLoaded', () => {
    getWeather(DEFAULT_CITY);
});
