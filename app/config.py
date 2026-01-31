from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable configuration."""

    mongo_username: str | None = Field(
        None, validation_alias="MONGO_USERNAME", description="MongoDB username"
    )
    mongo_password: str | None = Field(
        None, validation_alias="MONGO_PASSWORD", description="MongoDB password"
    )
    mongo_host: str | None = Field(None, validation_alias="MONGO_HOST")
    mongo_uri: str | None = Field(
        None,
        validation_alias="MONGO_URI",
        description="Optional direct MongoDB URI (overrides username/password/host)",
    )
    mongo_db: str = Field(..., validation_alias="MONGO_DATABASE")
    mongo_todo_collection: str = Field(..., validation_alias="MONGO_TODO_COLLECTION")
    mongo_user_collection: str = Field(..., validation_alias="MONGO_USER_COLLECTION")
    mongo_timeout: int = Field(..., validation_alias="MONGO_TIMEOUT")
    secret_key: str = Field(..., validation_alias="SECRET_KEY")
    password_algorithm: str = Field(..., validation_alias="PASSWORD_ALGORITHM")
    access_token_expire_seconds: int = Field(..., validation_alias="ACCESS_TOKEN_EXPIRE_SECONDS")
    refresh_token_expire_seconds: int = Field(..., validation_alias="REFRESH_TOKEN_EXPIRE_SECONDS")

    # Environment
    environment: str = Field("development", validation_alias="ENVIRONMENT")

    # Logging
    log_level: str = Field(
        "INFO",
        validation_alias="LOG_LEVEL",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    # Rate Limiting
    rate_limit_enabled: bool = Field(True, validation_alias="RATE_LIMIT_ENABLED")
    rate_limit_default: str = Field("100/minute", validation_alias="RATE_LIMIT_DEFAULT")
    rate_limit_auth: str = Field("5/minute", validation_alias="RATE_LIMIT_AUTH")
    redis_url: str | None = Field(None, validation_alias="REDIS_URL")

    # CORS Configuration
    cors_origins: str = Field(
        "*", validation_alias="CORS_ORIGINS", description="Comma-separated list of allowed origins"
    )
    cors_allow_credentials: bool = Field(False, validation_alias="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: str = Field("*", validation_alias="CORS_ALLOW_METHODS")
    cors_allow_headers: str = Field("*", validation_alias="CORS_ALLOW_HEADERS")

    # AI Configuration (Gemini API Proxy)
    gemini_api_key: str | None = Field(
        None, validation_alias="GEMINI_API_KEY", description="Google Gemini API key"
    )
    gemini_voice_model_id: str = Field(
        "gemini-2.5-flash-native-audio-latest",
        validation_alias="GEMINI_VOICE_MODEL_ID",
        description="Gemini Voice Model ID for streaming audio",
    )
    ai_rate_limit: str = Field(
        "10/minute", validation_alias="AI_RATE_LIMIT", description="AI endpoint rate limit"
    )

    # Observability
    otel_exporter_otlp_endpoint: str | None = Field(
        None, validation_alias="OTEL_EXPORTER_OTLP_ENDPOINT", description="OTLP Exporter Endpoint"
    )
    otel_service_name: str = Field("fasttodo", validation_alias="OTEL_SERVICE_NAME")
    metrics_bearer_token: str | None = Field(
        None,
        validation_alias="METRICS_BEARER_TOKEN",
        description="Optional bearer token for /metrics endpoint authentication",
    )

    model_config = SettingsConfigDict(env_file=".env")

    @field_validator("log_level", mode="before")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Validate and normalize log level.

        Args:
            value: Log level string (case-insensitive)

        Returns:
            Normalized uppercase log level

        Raises:
            ValueError: If log level is invalid
        """
        if not isinstance(value, str):
            raise ValueError(f"LOG_LEVEL must be a string, got {type(value).__name__}")

        normalized = value.upper()
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

        if normalized not in valid_levels:
            raise ValueError(
                f"Invalid LOG_LEVEL: {value}. Must be one of: {', '.join(sorted(valid_levels))}"
            )

        return normalized

    @model_validator(mode="after")
    def check_mongo_config(self) -> "Settings":
        """Validate that either MONGO_URI or all individual Mongo fields are set."""
        has_uri = bool(self.mongo_uri)
        has_individual = all([self.mongo_username, self.mongo_password, self.mongo_host])
        if not has_uri and not has_individual:
            raise ValueError(
                "Either MONGO_URI or all of MONGO_USERNAME, MONGO_PASSWORD, "
                "and MONGO_HOST must be set."
            )
        return self

    def _parse_comma_separated_config(self, value: str) -> list[str]:
        """Parse comma-separated configuration string to list.

        Args:
            value: Comma-separated string or "*" for wildcard

        Returns:
            List of parsed values, or ["*"] if value is "*"
        """
        if value == "*":
            return ["*"]
        return [item.strip() for item in value.split(",") if item.strip()]

    def get_cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string to list."""
        return self._parse_comma_separated_config(self.cors_origins)

    def get_cors_methods_list(self) -> list[str]:
        """Parse CORS methods from comma-separated string to list."""
        return self._parse_comma_separated_config(self.cors_allow_methods)

    def get_cors_headers_list(self) -> list[str]:
        """Parse CORS headers from comma-separated string to list."""
        return self._parse_comma_separated_config(self.cors_allow_headers)


def get_settings() -> Settings:
    return Settings()
