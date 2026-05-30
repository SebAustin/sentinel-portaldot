# Sentinel config — chain endpoints and demo multisig parameters

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    portaldot_ws_url: str = "ws://127.0.0.1:9944"
    portaldot_ss58_format: int = 42
    portaldot_type_registry_preset: str = "polkadot"
    multisig_threshold: int = 2
    proposer_seed: str = "//Alice"
    anthropic_api_key: str | None = None
    max_transfer_pot: float = 100.0
    pot_decimals: int = 14
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
