import aiohttp, asyncio
from typing import Optional, Dict, Any

from app.config import WEATHER_API, WEATHER_URL
from app.config import setup_logger

logger = setup_logger("weather_service", indent=6)


WEATHER_CODES = {
    "0": {"text": "Unknown", "emoji": "❓"},
    "1000": {"text": "Clear, Sunny", "emoji": "☀️"},
    "1100": {"text": "Mostly Clear", "emoji": "🌤️"}, 
    "1101": {"text": "Partly Cloudy", "emoji": "⛅"},
    "1102": {"text": "Mostly Cloudy", "emoji": "☁️"},
    "1001": {"text": "Cloudy", "emoji": "☁️"},
    "2000": {"text": "Fog", "emoji": "🌫️"},
    "2100": {"text": "Light Fog", "emoji": "🌫️"},
    "4000": {"text": "Drizzle", "emoji": "🌦️"},
    "4001": {"text": "Rain", "emoji": "🌧️"},
    "4200": {"text": "Light Rain", "emoji": "🌦️"}, 
    "4201": {"text": "Heavy Rain", "emoji": "⛈️"},
    "5000": {"text": "Snow", "emoji": "❄️"},
    "5001": {"text": "Flurries", "emoji": "🌨️"},
    "5100": {"text": "Light Snow", "emoji": "🌨️"},
    "5101": {"text": "Heavy Snow", "emoji": "❄️"},
    "6000": {"text": "Freezing Drizzle", "emoji": "🧊"},
    "6001": {"text": "Freezing Rain", "emoji": "🧊"},
    "6200": {"text": "Light Freezing Rain", "emoji": "🧊"},
    "6201": {"text": "Heavy Freezing Rain", "emoji": "🧊"},
    "7000": {"text": "Ice Pellets", "emoji": "🧊"},
    "7101": {"text": "Heavy Ice Pellets", "emoji": "🧊"}, 
    "7102": {"text": "Light Ice Pellets", "emoji": "🧊"},
    "8000": {"text": "Thunderstorm", "emoji": "⛈️"}
}

def extract_weather_summary(weather_data: dict) -> dict:
    """
    Extract a summary of the weather data.
    Args:
        weather_data (dict): Weather data in JSON format.
    Returns:
        dict: A summary of the weather data.
    """
    
    current = weather_data.get("current", {})
    forecast_days = weather_data.get("forecast", {}).get("forecastday", [])
    
    weather_summary = {
        "last_updated": current.get("last_updated", ""),
        "location": weather_data.get("location", {}).get("name"),
        "current": {
            "temp_c": current.get("temp_c"),
            "feelslike_c": current.get("feelslike_c"),
            "condition": current.get("condition", {}).get("text"),
            "wind_kph": current.get("wind_kph"),
            "wind_dir": current.get("wind_dir"),
            "humidity": current.get("humidity"),
            "pressure_mb": current.get("pressure_mb"),
            "uv": current.get("uv"),
            "precip_mm": current.get("precip_mm"),
            "cloud": current.get("cloud"),
            "gust_kph": current.get("gust_kph"),
        },
        "forecast": []
    }

    for day in forecast_days:
        day_data = day.get("day", {})
        astro = day.get("astro", {})
        weather_summary["forecast"].append({
            "date": day.get("date"),
            "maxtemp_c": day_data.get("maxtemp_c"),
            "mintemp_c": day_data.get("mintemp_c"),
            "avgtemp_c": day_data.get("avgtemp_c"),
            "condition": day_data.get("condition", {}).get("text"),
            "maxwind_kph": day_data.get("maxwind_kph"),
            "avghumidity": day_data.get("avghumidity"),
            "totalprecip_mm": day_data.get("totalprecip_mm"),
            "daily_chance_of_rain": day_data.get("daily_chance_of_rain"),
            "uv": day_data.get("uv"),
            "sunrise": astro.get("sunrise"),
            "sunset": astro.get("sunset"),
        })

    return weather_summary

def get_fallback_weather() -> Dict[str, Any]:
    """Return fallback weather data when API fails."""
    return {
        "status": "unavailable",
        "message": "Weather data temporarily unavailable ❓",
        "current": {
            "temp_c": None,
            "condition": "Unknown"
        },
        "forecast": []
    }

async def get_weather_call(timeout: int = 5, retries: int = 2) -> Optional[Dict[str, Any]]:
    """
    Fetch weather data with proper error handling and timeouts.
    
    Args:
        timeout: Request timeout in seconds
        retries: Number of retry attempts
        
    Returns:
        Weather data dict or None if all attempts fail
    """

    for attempt in range(retries):
        try:
            logger.info(f"Fetching weather data (attempt) {attempt + 1}/{retries}")

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(WEATHER_URL) as response:
                    if response.status != 200:
                        logger.warning(f"Weather API returned status {response.status}")
                        continue

                    weather_data = await response.json()

            if WEATHER_API == "freeweather":
                weather_data = extract_weather_summary(weather_data)

            if WEATHER_API == "tomorrow.io":
                weather_code = weather_data["data"]["values"]["weatherCode"]
                weather_data["data"]["values"]["weatherState"] = WEATHER_CODES.get(str(weather_code), "0")["text"]
                weather_data["data"]["values"]["weatherEmoji"] = WEATHER_CODES.get(str(weather_code), "0")["emoji"]
            
            logger.info("Weather data fetched successfully")
            return weather_data

        except Exception as e:
            logger.warning(f"Weather fetch failed: {e}")
            
        if attempt < retries - 1:
            wait_time = 1
            logger.info(f"Waiting {wait_time}s before retry...")
            await asyncio.sleep(wait_time)

    logger.error("All weather API attempts failed")
    return None

async def get_weather() -> Dict[str, Any]:
    """
    Get weather data with fallback handling.
    """
    try: 
        weather_data = await get_weather_call()
        if weather_data:
            return weather_data
        else:
            logger.info("Using fallback weather data")
            return get_fallback_weather()
    except Exception as e:
        logger.error(f"Critical error in weather service: {e}")
        return get_fallback_weather()


async def main() -> None:
    weather_data = await get_weather()
    print(weather_data)

if __name__ == '__main__':
    asyncio.run(main())