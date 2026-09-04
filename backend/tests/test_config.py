"""
Configuration tests — no database or network required.

Confirms Settings loads Stage 2's MongoDB fields with sensible defaults,
and that CORS/Mongo values can be overridden via environment variables
without touching backend/.env.
"""
from app.core.config import Settings


def test_mongodb_fields_default_to_empty_uri_and_named_db():
    settings = Settings(_env_file=None)
    assert settings.MONGODB_URI == ""
    assert settings.MONGODB_DB_NAME == "recoverai"


def test_mongodb_uri_can_be_overridden_via_env(monkeypatch):
    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:27017")
    monkeypatch.setenv("MONGODB_DB_NAME", "recoverai_test")

    settings = Settings(_env_file=None)

    assert settings.MONGODB_URI == "mongodb://localhost:27017"
    assert settings.MONGODB_DB_NAME == "recoverai_test"


def test_cors_origins_list_parses_comma_separated_string():
    settings = Settings(
        _env_file=None,
        CORS_ORIGINS="http://localhost:5173, http://127.0.0.1:5173",
    )
    assert settings.cors_origins_list == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]