from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    POSTGRES_USER: str = "recipe_user"
    POSTGRES_PASSWORD: str = "recipe_secret"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "recipe_db"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # MeiliSearch
    MEILI_HOST: str = "http://localhost:7700"
    MEILI_MASTER_KEY: str = "recipe_meili_master_key"

    # Auth
    SECRET_KEY: str = "change-me-to-a-random-string"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"

    # Upload
    UPLOAD_DIR: str = "/app/uploads"

    model_config = {"env_file": "../.env", "extra": "ignore"}


settings = Settings()
