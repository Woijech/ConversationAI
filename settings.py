from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    TELEGRAM_BOT_TOKEN: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    def get_llm_key(self):
        return self.OPENAI_API_KEY
    def get_telegram_bot_token(self):
        return self.TELEGRAM_BOT_TOKEN

settings = Settings()


