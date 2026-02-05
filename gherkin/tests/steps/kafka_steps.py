"""
Kafka шаги для тестирования.
Включает шаги для отправки сообщений в Kafka топики.
"""
from pytest_bdd import when, parsers


@when(parsers.parse('Отправить сообщение в кафку "{kafka_name}" в топик "{topic_name}" из файла "{file_path}"'))
def send_kafka_message_from_file(context, kafka_name, topic_name, file_path):
    """Отправка сообщения в Kafka топик из файла."""
    print(f"MOCK: Отправка сообщения в Kafka")
    print(f"MOCK: Кластер: {kafka_name}")
    print(f"MOCK: Топик: {topic_name}")
    print(f"MOCK: Файл сообщения: {file_path}")
    
    context["kafka"] = {
        "cluster": kafka_name,
        "topic": topic_name,
        "message_file": file_path,
        "sent": True
    }
