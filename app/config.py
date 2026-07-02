from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    CHROMA_PERSIST_DIR: str = "./data/chroma_db"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    class Config:
        env_file = ".env"

    from pydantic import model_validator

    @model_validator(mode="after")
    def sanitize_model_name(self) -> "Settings":
        if self.EMBEDDING_MODEL == "all-MiniLM-L6-v2":
            self.EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
        return self



settings = Settings()
