# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
for directory in [KNOWLEDGE_BASE_DIR, DATA_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
FILE_SEARCH_STORE_NAME = os.getenv("FILE_SEARCH_STORE_NAME", "polyguide-college-kb")

# Validation thresholds
MAX_UNANSWERED_QUEUE_SIZE = 500
MIN_GROUNDING_SOURCE_COUNT = 1
VERIFICATION_WARNING_DAYS = 90  # Warn if last_verified is older than this

# Categories
VALID_CATEGORIES = {
    "admission",
    "department",
    "fees",
    "facilities",
    "exam",
    "certificate",
    "contact",
    "other",
}

# File paths
FAQ_JSON_PATH = DATA_DIR / "faqs.json"
DEPARTMENTS_JSON_PATH = DATA_DIR / "departments.json"
CONTACTS_JSON_PATH = DATA_DIR / "contacts.json"
UNANSWERED_QUEUE_JSON_PATH = DATA_DIR / "unanswered_queue.json"