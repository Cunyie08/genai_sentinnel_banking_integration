import os
from dotenv import load_dotenv

# Load environment variables from a couple of possible .env files. The
# repository root `.env` contains database and API keys during local
# development, but some workflows might place the file inside `app/`.
# Try the root first, then fall back to app/.env so we don't raise errors
# when developers forget to duplicate the file.

root_env = os.path.join(os.getcwd(), ".env")
app_env = os.path.join(os.getcwd(), "app", ".env")
for env_path in (root_env, app_env):
    if os.path.exists(env_path):
        load_dotenv(env_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    # Use a dummy key for local development if not set, 
    # but warn the user.
    print("WARNING: SECRET_KEY is not set in .env. Using a dummy key for testing.")
    SECRET_KEY = "sentinel_super_secure_key_2026_dev"
