from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    OPENAI_API_KEY: str = ""
    MODEL_NAME: str = "gpt-4o"
    TEMPERATURE: float = 0.7
    GENERATIONS_PER_FEATURE: int = 1
    
    PROMPT_TEMPLATE: str = """
Ты опытный QA инженер.
Твоя задача - создать описание ручного теста на основе приведенного Gherkin feature файла.

Требования:
1. Язык: Строго Русский.
2. Формат: Абсолютно простой текст (Plain text). ЗАПРЕЩЕНО использовать Markdown (жирный, курсив, заголовки, списки через дефис или звездочку).
3. Стиль: Максимально простой.
4. Вывод: Верни ТОЛЬКО текст теста, без вступлений и пояснений.

Gherkin Feature:
{gherkin_content}

Текст теста:
"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Default configuration instance
config = Config()
