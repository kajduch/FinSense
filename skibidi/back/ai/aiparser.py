import json

from ai.ollamacli import OllamaClient
from ai.schemas import DOCUMENT_SCHEMA


class Parser:

    def __init__(self):
        self.ollama = OllamaClient(
            model="qwen3:8b"
        )

    def parse(self, text: str) -> dict:

        system_prompt = """
Ты — система структурирования документов.

Тебе передаётся текст документа, извлечённый из PDF.

Твоя задача:
1. Определить тип документа.
2. Найти важные данные.
3. Извлечь все транзакции.
4. Привести данные к заданной JSON-схеме.
5. Не придумывать отсутствующие данные.
6. Не удалять транзакции.
7. Сохранять суммы максимально точно.
8. Даты приводить к формату YYYY-MM-DD, если это возможно.

ДАТЫ НЕОБХОДИМЫ

Категорию транзакции определяй самостоятельно на основании описания ТОЛЬКО из этих 5 категорий:
- продукты
- транспорт
- рестораны
- цифровые товары
- одежда

Если информация отсутствует в документе, не выдумывай её.
"""

        prompt = f"""
Преобразуй следующий документ в структурированный JSON.

ТЕКСТ ДОКУМЕНТА:

{text}
"""

        response = self.ollama.generate(
            prompt=prompt,
            system=system_prompt,
            json_schema=DOCUMENT_SCHEMA
        )

        try:
            return json.loads(response)

        except json.JSONDecodeError as e:
            raise ValueError(
                f"Ollama вернула некорректный JSON: {e}\n"
                f"Ответ модели:\n{response}"
            )