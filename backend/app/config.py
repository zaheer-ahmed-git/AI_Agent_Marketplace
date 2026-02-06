from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = (
        "postgresql+psycopg://marketplace:marketplace@localhost:5432/marketplace"
    )
    jwt_secret: str = "dev-only-change-me-please-local-only"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24
    openai_api_key: str = ""
    use_llm: bool = False
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


settings = Settings()
