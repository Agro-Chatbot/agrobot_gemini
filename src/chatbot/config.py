import os
from pathlib import Path

from dotenv import load_dotenv

# .env en la raíz del proyecto (dos niveles arriba de src/chatbot/)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-6")

_csv_path = os.getenv("CSV_PATH", "data/sample.csv")
CSV_PATH = Path(_csv_path)
if not CSV_PATH.is_absolute():
    CSV_PATH = PROJECT_ROOT / CSV_PATH

OUTPUT_DIR = PROJECT_ROOT / "output"
