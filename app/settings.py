import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_WEBHOOK_SECRET = os.getenv("RESEND_WEBHOOK_SECRET")
APP_URL = os.getenv("APP_URL", "https://sentinnelbanking.com")
EMAIL_FROM = os.getenv("EMAIL_FROM", "Sentinel Bank <onboarding@sentinnelbanking.com>")