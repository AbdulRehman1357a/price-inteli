from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Retail Pricing Intelligence Platform"
    app_version: str = "1.0.0"
    service_name: str = "retail-pricing-api"
    app_env: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    jwt_secret_key: str = "change-me-in-secrets-manager"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    remember_me_refresh_token_expire_days: int = 30

    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_database: str = "rpip_db"
    mysql_user: str = "rpip_user"
    mysql_password: str = "rpip_password"

    redis_url: str = "redis://localhost:6379/0"

    cors_origins: str = "http://localhost:5173"

    aws_region: str = "us-east-1"
    s3_bucket_name: str = ""
    # Fallback storage when s3_bucket_name is unset (local dev/test) — see
    # app/storage/__init__.py's get_storage_adapter().
    local_storage_dir: str = "var/storage"

    max_import_file_size_mb: int = 20

    # Base URL of the frontend app — used to build the public price-display
    # link that QR/Web outputs point to (app/outputs/*, app/services/output_job_service.py).
    public_base_url: str = "http://localhost:5173"

    # ESL device MQTT broker — app/services/mqtt_publisher.py. Publishing is
    # best-effort (see _broker_reachable there): no broker running locally
    # is expected in dev, and the ESL simulator's acknowledgement is
    # simulated synchronously regardless (see app/integrations/esl_simulator).
    mqtt_broker_host: str = "localhost"
    mqtt_broker_port: int = 1883
    mqtt_topic_prefix: str = "retail"

    # Symmetric key (Fernet) encrypting ESLIntegration.configuration_encrypted
    # at rest — app/core/crypto.py. Dev-only default, same pattern as
    # jwt_secret_key: real deployments source this from AWS Secrets Manager.
    esl_credentials_encryption_key: str = "GiGeYdXUIRHcfnliSeP1fCccJiVwUqFj8d8ZolXnd_E="

    @property
    def database_url(self) -> str:
        user = quote_plus(self.mysql_user)
        password = quote_plus(self.mysql_password)
        return f"mysql+pymysql://{user}:{password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"

    @property
    def celery_broker_url(self) -> str:
        return self.redis_url

    @property
    def celery_result_backend(self) -> str:
        return self.redis_url

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
