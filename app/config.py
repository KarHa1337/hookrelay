import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hookrelay.db")
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))
MAX_PAYLOAD_BYTES = int(os.getenv("MAX_PAYLOAD_BYTES", "25000"))
