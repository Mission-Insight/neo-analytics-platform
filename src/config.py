from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

NASA_API_KEY = os.getenv("NASA_API_KEY")
DB_PATH = os.getenv("DATABASE_PATH")

if not NASA_API_KEY:
    raise ValueError(
        "NASA_API_KEY was not found. Make sure your .env file"
        "exists in the project root and contains NASA_API_KEY=your_api_key_here."
    )

if not DB_PATH:
    raise ValueError(
        "DATABASE_PATH was not found. Make sure your .env file"
        "exists in the project root and contains DATABASE_PATH=your_database_path_here."
    )

DB_PATH = Path(DB_PATH)
