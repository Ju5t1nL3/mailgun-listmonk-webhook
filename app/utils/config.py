from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MAILGUN_SIGNING_KEY: str

    LISTMONK_URL: str
    LISTMONK_API_USER: str
    LISTMONK_API_TOKEN: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
