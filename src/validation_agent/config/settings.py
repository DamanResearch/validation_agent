from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    catalog: str = "metadata_discovery"
    schema: str = "validation_agent"
    model_endpoint: str = ""

    @property
    def fq(self) -> str:
        return f"{self.catalog}.{self.schema}"


settings = Settings()
