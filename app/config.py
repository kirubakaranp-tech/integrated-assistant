import os

from dotenv import load_dotenv

load_dotenv()

CHROMA_DIR = os.getenv("CHROMA_DIR", "data/chroma")
COLLECTION_NAME = "documents"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120

MAX_FILE_SIZE_MB = 20

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TOP_K = 4
MAX_DISTANCE = 1.4
MEMORY_SIZE = 5

CRM_URL = os.getenv("CRM_URL", "http://127.0.0.1:8001")
CRM_TIMEOUT = 5

DATABASE_URL = os.getenv("DATABASE_URL", "")

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500").split(",")
    if origin.strip()
]
