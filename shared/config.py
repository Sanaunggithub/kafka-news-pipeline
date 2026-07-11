from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int
    POSTGRES_HOST: str = "postgres"

    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"

    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333

    API_PORT: int = 8000

    KAFKA_SECURITY_PROTOCOL: str = "PLAINTEXT"
    KAFKA_SSL_CAFILE: str = ""
    KAFKA_SSL_CERTFILE: str = ""
    KAFKA_SSL_KEYFILE: str = ""
    QDRANT_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def postgres_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()