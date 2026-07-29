import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./creative_reasoning.db")

    # ── IBM watsonx.ai connection ─────────────────────────────────────────────
    # Required for live Granite: set these in a .env file or environment.
    # GRANITE_API_URL  — watsonx.ai regional endpoint
    #                    e.g. https://us-south.ml.cloud.ibm.com
    # GRANITE_API_KEY  — IBM Cloud API key
    # WATSONX_PROJECT_ID — watsonx.ai project ID (from the project settings page)
    GRANITE_API_URL: str = os.getenv(
        "GRANITE_API_URL", "https://us-south.ml.cloud.ibm.com"
    )
    GRANITE_API_KEY: str = os.getenv("GRANITE_API_KEY", "")
    WATSONX_PROJECT_ID: str = os.getenv("WATSONX_PROJECT_ID", "")

    # granite-13b-instruct-v2 is the recommended general-purpose Granite model.
    # For faster/cheaper responses use ibm/granite-7b-lab.
    GRANITE_MODEL_ID: str = os.getenv(
        "GRANITE_MODEL_ID", "ibm/granite-13b-instruct-v2"
    )

    SEED_DATA_PATH: str = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "app", "data", "seed"
    )

    # When True (default) the application uses MockGraniteAdapter so it works
    # offline.  Set to False in .env to activate the real watsonx.ai client.
    USE_MOCK_GRANITE: bool = True

    model_config = {"env_file": ".env"}


settings = Settings()
