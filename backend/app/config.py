import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///haunsla.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ]
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
    SCRAPE_INTERVAL_MINUTES = int(os.getenv("SCRAPE_INTERVAL_MINUTES", "60"))
    RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
    ALERT_FROM_EMAIL = os.getenv("ALERT_FROM_EMAIL", "alerts@haunsla.pk")
    SEED_DEMO_JOBS = os.getenv("SEED_DEMO_JOBS", "1") == "1"
