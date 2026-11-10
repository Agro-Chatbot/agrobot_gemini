import os
from pathlib import Path

from dotenv import load_dotenv

# .env en la raíz del proyecto (dos niveles arriba de src/chatbot/)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.8-flash")

_csv_path = os.getenv("CSV_PATH", "data/sample.csv")
CSV_PATH = Path(_csv_path)
if not CSV_PATH.is_absolute():
    CSV_PATH = PROJECT_ROOT / CSV_PATH

_precip_csv_path = os.getenv("PRECIP_CSV_PATH", "data/Campo_precipitaciones_2018-2026.csv")
PRECIP_CSV_PATH = Path(_precip_csv_path)
if not PRECIP_CSV_PATH.is_absolute():
    PRECIP_CSV_PATH = PROJECT_ROOT / PRECIP_CSV_PATH

OUTPUT_DIR = PROJECT_ROOT / "output"
