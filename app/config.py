from dotenv import load_dotenv
from pathlib import Path
import os

# --- Load .env from actual project root ---
# Go up one level from readme_gen to get to the actual project root
BASE_DIR = Path(__file__).parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# --- API Keys ---
FREEWEATHER_API_KEY = os.getenv("FREEWEATHER_API_KEY")
TOMORROWIO_API_KEY = os.getenv("TOMORROWIO_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# --- Google Gemini ---
MODEL_NAME = "gemini-2.5-flash"
MODEL_NAME_PRO = "gemini-2.5-pro"
MODEL_PROVIDER = "google_genai"

DEFAULT_RESPONSE = "Unable to generate response at this time."

# --- Database ---
DATABASE_URL = "sqlite+aiosqlite:///app/data/app.db"

# --- Paths ---
APP_DIR = BASE_DIR / "app"
RESOURCES_DIR = APP_DIR / "resources"
UI_DIR = APP_DIR / "presentation/ui"
DATA_DIR = APP_DIR / "data"
TEMPLATES_DIR = RESOURCES_DIR / "templates"
REPO_DIR = Path(os.environ.get("REPO_DIR", "/home/alyson/Applications/Obsidian/Vaults"))

README_PATH = APP_DIR / "presentation/ui/README.md"
COMMIT_MSG_PATH = APP_DIR / "presentation/ui/commit.txt"
TIME_DARK_SVG_PATH = APP_DIR / "presentation/ui/time-dark.svg"
TIME_LIGHT_SVG_PATH = APP_DIR / "presentation/ui/time-light.svg"

# --- Free Weather API settings
LOCATION = "Moscow"
FREEWEATHER_URL = f"http://api.weatherapi.com/v1/current.json?key={FREEWEATHER_API_KEY}&q={LOCATION}&aqi=no"

# --- Tomorrow.io API settings
LOCATION = "Zyuzino,Moscow,Russia"
TOMORROWIO_URL = f"https://api.tomorrow.io/v4/weather/realtime?location={LOCATION}&apikey={TOMORROWIO_API_KEY}"

# --- Weather API selection
WEATHER_API = "tomorrow.io"
WEATHER_URL = TOMORROWIO_URL

# --- Github ---
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")
REMOTE_URL = "https://github.com/alyson-mei/obsidian-memo"

# --- General settings ---
NUM_LAST_COMMIT_MSG = 25
NUM_NEW_COMMIT_MSG = 15

NUM_LAST_SEARCH_MSG = 35

NUM_LAST_JOURNAL_MSG = 10

TIME_MESSAGE_INTERVAL = 1                     # minutes - every minute
WEATHER_COMMIT_INTERVAL = NUM_NEW_COMMIT_MSG  # minutes - every 15 minutes (quarters)
BING_MESSAGE_INTERVAL = 60                    # minutes - every hour
GEO_MESSAGE_TIME = "10:00"                    # daily at 10:00
GEO_MESSAGE_HOUR = 10
GEO_MESSAGE_MINUTE = 0
JOURNAL_MESSAGE_TIME = "23:00"                  
JOURNAL_MESSAGE_HOUR = 23
JOURNAL_MESSAGE_MINUTE = 00

MAX_COMMITS_BEFORE_REBASE = 720
DEFAULT_BRANCH = "main"

FORCE_PUSH_ON_STARTUP = True  # Set to True if you want to force push on startup
FORCE_PUSH_SCHEDULE_HOUR = None  # Set to an hour (0-23) for daily force push
FORCE_PUSH_SCHEDULE_MINUTE = None  # Set to a minute (0-59) for daily force push


# --- Logging ---
import logging
import colorlog # type: ignore

colorlog.escape_codes.escape_codes.update({
   # Light/pastel colors using standard ANSI
   'light_green': '\033[92m',
   'light_blue': '\033[94m', 
   'light_purple': '\033[95m',
   'light_cyan': '\033[96m',
   
   # Pastel colors using 256-color palette
   'mint': '\033[38;5;121m',
   'sky_blue': '\033[38;5;117m',
   'lavender': '\033[38;5;183m',
   'peach': '\033[38;5;216m',
   'coral': '\033[38;5;209m',
   'pink': '\033[38;5;205m',
   'sage': '\033[38;5;151m',
   'powder_blue': '\033[38;5;152m',
   'lilac': '\033[38;5;189m',
   'seafoam': '\033[38;5;158m',
   'periwinkle': '\033[38;5;147m',
   'rose': '\033[38;5;217m',
   'aqua': '\033[38;5;159m',
   'blush': '\033[38;5;224m',
   'teal': '\033[38;5;123m',
   'soft_yellow': '\033[38;5;229m',
   'pale_green': '\033[38;5;194m',
   'ice_blue': '\033[38;5;195m',
   'cream': '\033[38;5;230m',
   'dusty_rose': '\033[38;5;181m',
})

logger_settings = {
    'database': 
        {'color': 'green', "indent": 6},
    'service':         
        {'color': 'cyan', "indent": 6},
    'generator': 
        {'color': 'lavender', "indent": 4},
    'ui':
        {'color': 'peach', "indent": 2},
    'main':
        {'color': 'cream', 'indent': 0},
    'default':
        {'color': 'cream', "indent": 0}
}

class CustomFormatter(colorlog.ColoredFormatter):
    def format(self, record):
        settings = logger_settings['default']
        for postfix, config in logger_settings.items():
            if postfix != 'default' and record.name.endswith(postfix):
                settings = config
                break
        self.log_colors = {record.levelname: settings['color']}
        return super().format(record)
    
def setup_logger(name: str, indent: int = 0) -> logging.Logger:
    handler = colorlog.StreamHandler()
    
    formatter = CustomFormatter(  # ← Use your custom formatter
        (" " * indent) + "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        reset=True,
        log_colors={}  # Empty, will be set in format()
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False
    return logger
