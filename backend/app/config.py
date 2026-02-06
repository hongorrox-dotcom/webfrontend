from typing import List

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    _USING_PYDANTIC_SETTINGS = True
except ModuleNotFoundError:
    # Fallback for environments without pydantic-settings installed.
    # pydantic.v1 ships with pydantic v2 and still supports BaseSettings.
    from pydantic.v1 import BaseSettings  # type: ignore

    SettingsConfigDict = dict  # type: ignore
    _USING_PYDANTIC_SETTINGS = False


class Settings(BaseSettings):
    if _USING_PYDANTIC_SETTINGS:
        model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    else:
        class Config:
            env_file = ".env"
            extra = "ignore"

    MODEL_PATH: str = "./models/dornodjinkencopy2.mdl"
    DEMO_MODE_AUTO: int = 1

    # ===== OpenAI =====
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_CHAT_PATH: str = "/chat/completions"

    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    # Allow local network dev URLs like http://192.168.x.x:5173
    ALLOWED_ORIGIN_REGEX: str = r"^http://(localhost|127\\.0\\.0\\.1|192\\.168\\.\d+\\.\d+):5173$"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [s.strip() for s in self.ALLOWED_ORIGINS.split(",") if s.strip()]

    @property
    def allowed_origin_regex(self) -> str | None:
        value = (self.ALLOWED_ORIGIN_REGEX or "").strip()
        return value or None


settings = Settings()
