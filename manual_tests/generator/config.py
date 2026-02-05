import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    GENERATIONS_PER_FEATURE: int = int(os.getenv("GENERATIONS_PER_FEATURE", "1"))
    
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

# Default configuration instance
config = Config()
