"""
weather_gen.py

This generator module creates human-friendly weather messages using large language models (LLMs).
It takes structured weather data and the current part of day, crafts a prompt, and uses an LLM to generate
a concise, expressive weather summary with a moody reflection. The result is saved to the database for use
in dashboards, journals, or other features.

Key features:
- Adapts output to the available weather data, omitting irrelevant or missing fields.
- Uses natural, interpretive language and emojis for clarity and emotional tone.
- Adds a short, introspective weather reflection tailored to the day's conditions.
- Integrates with the database: saves new weather messages and manages table size with truncation.
- Provides robust logging and error handling throughout the process.

Typical usage:
- Called by scheduled jobs or user actions to keep weather summaries up to date.
- Can be run as a standalone script for demonstration or testing.

Dependencies:
- app.services.llm (for LLM interaction)
- app.services.part_of_day (for contextual time-of-day info)
- app.data.database, app.data.repository, app.data.models (for DB operations)
- app.config (for configuration and logger setup)
"""

from datetime import datetime

from app.services.llm import call_llm
from app.services.part_of_day import get_part_of_day_description
from app.data.repository import RepositoryFactory
from app.data.models import Weather
from app.data.database import AsyncSessionLocal
from app.config import WEATHER_API, setup_logger

logger = setup_logger("weather_generator", indent=4)

common_system_prompt = """
You are a weather assistant. Your task is to read structured weather data in JSON format and generate a human-friendly report. 
Your key goal is **adaptability**: interpret the data deeply, and output only what is meaningful and relevant.

## Workflow (you MUST follow this thought process before writing):

1. **Analyze** the input data:
   - Determine which fields are present and which are missing.
   - Consider whether any fields have zero or irrelevant values (e.g. 0 precipitation, low UV, etc.).

2. **Decide what to include**:
   - Choose only the fields that are significant for a human weather summary.
   - Skip values that are not helpful or would clutter the message.

3. **Decide how to phrase them**:
   - Don’t just state the raw value.
   - Use **natural**, **interpretive** descriptions: e.g. “a light breeze”, “moderate UV”, “low visibility”, “soft rain”.
   - Adjust vocabulary based on intensity and context. Avoid technical jargon.
   - Think like a person explaining the weather to a friend in a simple and expressive way.

4. **Format your message**:
   - Start with a headline: "Weather in <location> (<date>, <local time>)"
   - Present values with casual formatting and emojis.
   - Use `<br>` for line breaks between lines.
   - At the end, add a short weather reflection consisting of a simple, everyday-style title (e.g. “🌧️ Rainy and Quiet Morning”), followed by 1–2 sentences with a soft, moody tone — something introspective, cozy, or evocative, matching the day's weather conditions.

5. **Time of day debug**: 22 is late evening, 23 is night, 0-4 is night, 5 is early morning   

## Rules:
- NEVER output “None”, “null”, or field names with no value.
- Do NOT include all fields just because they exist in the input — be selective.
- Use simple, everyday language.
- Always adapt the phrasing and structure to the specific data given.

## Output Style:
- Casual and human, not robotic.
- Emojis are welcome.
- Prioritize clarity, meaning, and emotional tone over completeness.

## Example:
(Use this only to understand the formatting and tone — your actual output should depend fully on the input data)
"""

freeweather_example_prompt = """
* Input:
{'last_updated': '2025-06-14 14:00', 'location': 'Moscow', 'current': {'temp_c': 14.2, 'feelslike_c': 12.9, 'condition': 'Partly cloudy', 'wind_kph': 16.9, 'wind_dir': 'N', 'humidity': 94, 'pressure_mb': 1008.0, 'uv': 0.5, 'precip_mm': 1.88, 'cloud': 75, 'gust_kph': 24.7}, 'forecast': []}
* Output:
Weather in Moscow (2025-06-14, 14:00)

- 🌡️ Temperature: 14.2° (feels like 12.9°)
- 💨 Wind: northern breeze
- 💧 Humidity: 94%
- 🌦️ Condition: light rain 
- 📉 Pressure: 1008 mb
- 🌞 UV index: soft UV 0.5
"""

tomorrowio_example_prompt = """
*Input:
{"data":{"time":"2025-06-20T08:34:00Z","values":{"altimeterSetting":997.97,"cloudBase":0.8,"cloudCeiling":1.5,"cloudCover":87,"dewPoint":11.2,"freezingRainIntensity":0,"humidity":89,"precipitationProbability":100,"pressureSeaLevel":998.59,"pressureSurfaceLevel":980.14,"rainIntensity":1.83,"sleetIntensity":0,"snowIntensity":0,"temperature":13,"temperatureApparent":13,"uvHealthConcern":1,"uvIndex":4,"visibility":4.99,"weatherCode":Light Rain,"windDirection":309,"windGust":7.6,"windSpeed":3.5}},"location":{"lat":55.653141021728516,"lon":37.58674621582031,"name":"район Зюзино, Москва, Центральный федеральный округ, Россия","type":"administrative"}}
*Output:
Weather in Moscow (2025-06-20, 11:34)

🌡️ Temp: 13°C (feels like 13°C) <br>  
🌧️ Condition: Light rain (1.8 mm/h) <br> 
💨 Wind: NW breeze at 3.5 m/s, gusts up to 7.6 m/s <br> 
💧 Humidity: 89% <br>
📉 Pressure: 998 mb (sea level), 980 mb (surface) <br>  
☁️ Cloud cover: 87% (low base at 0.8 km) <br> 
🌞 UV index: 4 (moderate) <br> 
👁 Visibility: 5 km <br> 

🌧️ Rainy and Quiet Morning <br>
A gloomy morning with light rain and a chill in the air. Perfect time to wrap yourself in a blanket or dive into some quiet, focused work.
"""

prompt_selection = {"freeweather": freeweather_example_prompt, "tomorrow.io": tomorrowio_example_prompt}
hour = datetime.now().hour
part_of_day = get_part_of_day_description(hour)

system_prompt = common_system_prompt + prompt_selection[WEATHER_API]
human_prompt = "Weather data: \n {weather_data} \n Part of day: {part_of_day}"

async def generate_weather_message(weather_data: dict) -> str:
   """
   Generate a human-friendly weather message using LLM and save it to the database.

   Args:
      weather_data (dict): Structured weather data to be summarized.

   Returns:
      str: Generated weather message, or an error message if generation fails.
   """
   
   logger.info("Generating weather message")

   fhuman_prompt = human_prompt.format(
      weather_data=weather_data,
      part_of_day=part_of_day
      )
   
   response_content = await call_llm(system_prompt, fhuman_prompt, default_response="")

   if response_content == "":
      logger.error("Failed to generate weather message")
      return "Failed to generate weather message"
   
   logger.info(f"Saving weather message to database")
   try:
      async with AsyncSessionLocal() as session:
         repo = RepositoryFactory(session).get_repository(Weather)
         await repo.truncate(max_entries=128, keep_entries=64)
         await repo.create(message=response_content)
   except Exception as e:
        logger.error(f"Failed to save weather message: {e}")
   logger.info("Weather message saved to the database.")

   return response_content

async def main() -> None:
   from app.services.weather import get_weather
   weather_data = await get_weather()
   response_content = await generate_weather_message(weather_data)
   print(response_content)

if __name__ == '__main__':
   import asyncio
   asyncio.run(main())