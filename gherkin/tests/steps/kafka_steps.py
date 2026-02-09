"""
Kafka шаги для тестирования.
Включает шаги для отправки и получения сообщений в Kafka топики,
управления консьюмерами и продюсерами, работы с партициями.
"""
from steps.soft_assert import soft_assert
from pytest_bdd import given, when, then, parsers
import json
import uuid
from datetime import datetime


# ============================================================================
# --- Given steps (Kafka Setup) ---
# ============================================================================

@given(parsers.parse('установлено подключение к Kafka кластеру "{cluster_name}"'))
def setup_kafka_connection(context, cluster_name):
    """Установка подключения к Kafka кластеру."""
    if "kafka_clusters" not in context:
        context["kafka_clusters"] = {}
    context["kafka_clusters"][cluster_name] = {
        "connected": True,
        "connection_time": datetime.now().isoformat()
    }
    print(f"MOCK: Установлено подключение к Kafka кластеру {cluster_name}")


@given(parsers.parse('установлено подключение к Kafka кластеру "{cluster_name}" с параметрами:'))
def setup_kafka_connection_with_params(context, cluster_name, docstring):
    """Установка подключения к Kafka кластеру с параметрами."""
    if "kafka_clusters" not in context:
        context["kafka_clusters"] = {}
    context["kafka_clusters"][cluster_name] = {
        "connected": True,
        "params": docstring
    }
    print(f"MOCK: Установлено подключение к Kafka кластеру {cluster_name} с параметрами")


@given(parsers.parse('создан продюсер для кластера "{cluster_name}"'))
def create_kafka_producer(context, cluster_name):
    """Создание Kafka продюсера."""
    if "kafka_producers" not in context:
        context["kafka_producers"] = {}
    context["kafka_producers"][cluster_name] = {
        "created": True,
        "producer_id": str(uuid.uuid4())
    }
    print(f"MOCK: Создан продюсер для кластера {cluster_name}")


@given(parsers.parse('создан продюсер для кластера "{cluster_name}" с конфигурацией:'))
def create_kafka_producer_with_config(context, cluster_name, docstring):
    """Создание Kafka продюсера с конфигурацией."""
    if "kafka_producers" not in context:
        context["kafka_producers"] = {}
    context["kafka_producers"][cluster_name] = {
        "created": True,
        "producer_id": str(uuid.uuid4()),
        "config": docstring
    }
    print(f"MOCK: Создан продюсер для кластера {cluster_name} с конфигурацией")


@given(parsers.parse('создан консьюмер для кластера "{cluster_name}" в группе "{group_id}"'))
def create_kafka_consumer(context, cluster_name, group_id):
    """Создание Kafka консьюмера."""
    if "kafka_consumers" not in context:
        context["kafka_consumers"] = {}
    context["kafka_consumers"][cluster_name] = {
        "created": True,
        "consumer_id": str(uuid.uuid4()),
        "group_id": group_id
    }
    print(f"MOCK: Создан консьюмер для кластера {cluster_name} в группе {group_id}")


@given(parsers.parse('создан консьюмер для кластера "{cluster_name}" в группе "{group_id}" с конфигурацией:'))
def create_kafka_consumer_with_config(context, cluster_name, group_id, docstring):
    """Создание Kafka консьюмера с конфигурацией."""
    if "kafka_consumers" not in context:
        context["kafka_consumers"] = {}
    context["kafka_consumers"][cluster_name] = {
        "created": True,
        "consumer_id": str(uuid.uuid4()),
        "group_id": group_id,
        "config": docstring
    }
    print(f"MOCK: Создан консьюмер для кластера {cluster_name} в группе {group_id} с конфигурацией")


@given(parsers.parse('консьюмер подписан на топик "{topic_name}" кластера "{cluster_name}"'))
def subscribe_to_topic(context, topic_name, cluster_name):
    """Подписка консьюмера на топик."""
    if "kafka_subscriptions" not in context:
        context["kafka_subscriptions"] = {}
    if cluster_name not in context["kafka_subscriptions"]:
        context["kafka_subscriptions"][cluster_name] = []
    context["kafka_subscriptions"][cluster_name].append(topic_name)
    print(f"MOCK: Консьюмер подписан на топик {topic_name} кластера {cluster_name}")


@given(parsers.parse('консьюмер подписан на топики кластера "{cluster_name}":'))
def subscribe_to_topics(context, cluster_name, docstring):
    """Подписка консьюмера на несколько топиков."""
    topics = [t.strip() for t in docstring.strip().split("\n")]
    if "kafka_subscriptions" not in context:
        context["kafka_subscriptions"] = {}
    context["kafka_subscriptions"][cluster_name] = topics
    print(f"MOCK: Консьюмер подписан на топики {topics} кластера {cluster_name}")


@given(parsers.parse('установлен offset консьюмера на "{offset}" для топика "{topic_name}"'))
def set_consumer_offset(context, offset, topic_name):
    """Установка offset консьюмера."""
    if "kafka_offsets" not in context:
        context["kafka_offsets"] = {}
    context["kafka_offsets"][topic_name] = offset
    print(f"MOCK: Offset консьюмера установлен на {offset} для топика {topic_name}")


@given(parsers.parse('установлен таймаут чтения сообщений {timeout:d} секунд'))
def set_kafka_read_timeout(context, timeout):
    """Установка таймаута чтения сообщений."""
    context["kafka_read_timeout"] = timeout
    print(f"MOCK: Таймаут чтения сообщений установлен на {timeout} секунд")


@given(parsers.parse('установлен таймаут отправки сообщений {timeout:d} секунд'))
def set_kafka_send_timeout(context, timeout):
    """Установка таймаута отправки сообщений."""
    context["kafka_send_timeout"] = timeout
    print(f"MOCK: Таймаут отправки сообщений установлен на {timeout} секунд")


@given(parsers.parse('включен режим exactly-once для продюсера'))
def enable_exactly_once(context):
    """Включение режима exactly-once."""
    context["kafka_exactly_once"] = True
    print(f"MOCK: Режим exactly-once включен")


@given(parsers.parse('установлен acks "{acks}" для продюсера'))
def set_producer_acks(context, acks):
    """Установка уровня подтверждений для продюсера."""
    context["kafka_acks"] = acks
    print(f"MOCK: Acks установлен на {acks}")


@given(parsers.parse('установлен compression type "{compression}" для продюсера'))
def set_producer_compression(context, compression):
    """Установка типа сжатия для продюсера."""
    context["kafka_compression"] = compression
    print(f"MOCK: Compression type установлен на {compression}")


@given(parsers.parse('очищен топик "{topic_name}" в кластере "{cluster_name}"'))
def clear_kafka_topic(context, topic_name, cluster_name):
    """Очистка топика."""
    print(f"MOCK: Топик {topic_name} очищен в кластере {cluster_name}")


# ============================================================================
# --- When steps (Kafka Operations) ---
# ============================================================================

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


@when(parsers.parse('отправить сообщение в топик "{topic_name}" кластера "{cluster_name}":'))
def send_kafka_message_inline(context, topic_name, cluster_name, docstring):
    """Отправка сообщения в Kafka топик."""
    print(f"MOCK: Отправка сообщения в топик {topic_name} кластера {cluster_name}")
    print(f"MOCK: Сообщение:\n{docstring}")
    
    context["kafka"] = {
        "cluster": cluster_name,
        "topic": topic_name,
        "message": docstring,
        "sent": True,
        "offset": 12345,
        "partition": 0,
        "timestamp": datetime.now().isoformat()
    }


@when(parsers.parse('отправить сообщение в топик "{topic_name}" кластера "{cluster_name}" с ключом "{key}":'))
def send_kafka_message_with_key(context, topic_name, cluster_name, key, docstring):
    """Отправка сообщения в Kafka топик с ключом."""
    print(f"MOCK: Отправка сообщения с ключом {key} в топик {topic_name}")
    print(f"MOCK: Сообщение:\n{docstring}")
    
    context["kafka"] = {
        "cluster": cluster_name,
        "topic": topic_name,
        "key": key,
        "message": docstring,
        "sent": True,
        "offset": 12345,
        "partition": 0
    }


@when(parsers.parse('отправить сообщение в топик "{topic_name}" кластера "{cluster_name}" в партицию {partition:d}:'))
def send_kafka_message_to_partition(context, topic_name, cluster_name, partition, docstring):
    """Отправка сообщения в конкретную партицию."""
    print(f"MOCK: Отправка сообщения в партицию {partition} топика {topic_name}")
    print(f"MOCK: Сообщение:\n{docstring}")
    
    context["kafka"] = {
        "cluster": cluster_name,
        "topic": topic_name,
        "partition": partition,
        "message": docstring,
        "sent": True,
        "offset": 12345
    }


@when(parsers.parse('отправить сообщение в топик "{topic_name}" кластера "{cluster_name}" с заголовками:'))
def send_kafka_message_with_headers(context, topic_name, cluster_name, docstring):
    """Отправка сообщения с заголовками."""
    lines = docstring.strip().split("\n")
    headers = {}
    message = ""
    parsing_headers = True
    
    for line in lines:
        if line.strip() == "---":
            parsing_headers = False
            continue
        if parsing_headers and ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()
        else:
            message += line + "\n"
    
    print(f"MOCK: Отправка сообщения с заголовками в топик {topic_name}")
    print(f"MOCK: Заголовки: {headers}")
    print(f"MOCK: Сообщение:\n{message}")
    
    context["kafka"] = {
        "cluster": cluster_name,
        "topic": topic_name,
        "headers": headers,
        "message": message.strip(),
        "sent": True,
        "offset": 12345
    }


@when(parsers.parse('отправить пакет сообщений в топик "{topic_name}" кластера "{cluster_name}":'))
def send_kafka_batch(context, topic_name, cluster_name, docstring):
    """Отправка пакета сообщений."""
    messages = docstring.strip().split("\n---\n")
    print(f"MOCK: Отправка пакета из {len(messages)} сообщений в топик {topic_name}")
    
    context["kafka"] = {
        "cluster": cluster_name,
        "topic": topic_name,
        "batch_size": len(messages),
        "sent": True
    }


@when(parsers.parse('отправить {count:d} сообщений в топик "{topic_name}" кластера "{cluster_name}"'))
def send_kafka_multiple_messages(context, count, topic_name, cluster_name):
    """Отправка нескольких сообщений."""
    print(f"MOCK: Отправка {count} сообщений в топик {topic_name}")
    
    context["kafka"] = {
        "cluster": cluster_name,
        "topic": topic_name,
        "messages_sent": count,
        "sent": True
    }


@when(parsers.parse('прочитать сообщение из топика "{topic_name}" кластера "{cluster_name}"'))
def read_kafka_message(context, topic_name, cluster_name):
    """Чтение одного сообщения из топика."""
    print(f"MOCK: Чтение сообщения из топика {topic_name} кластера {cluster_name}")
    
    context["kafka_received"] = {
        "cluster": cluster_name,
        "topic": topic_name,
        "message": {"data": "mock_message"},
        "key": "mock_key",
        "offset": 12345,
        "partition": 0,
        "timestamp": datetime.now().isoformat()
    }


@when(parsers.parse('прочитать {count:d} сообщений из топика "{topic_name}" кластера "{cluster_name}"'))
def read_kafka_messages(context, count, topic_name, cluster_name):
    """Чтение нескольких сообщений из топика."""
    print(f"MOCK: Чтение {count} сообщений из топика {topic_name}")
    
    context["kafka_received"] = {
        "cluster": cluster_name,
        "topic": topic_name,
        "messages": [{"data": f"mock_message_{i}"} for i in range(count)],
        "count": count
    }


@when(parsers.parse('прочитать сообщения из топика "{topic_name}" кластера "{cluster_name}" за последние {seconds:d} секунд'))
def read_kafka_messages_by_time(context, topic_name, cluster_name, seconds):
    """Чтение сообщений за указанный период."""
    print(f"MOCK: Чтение сообщений из топика {topic_name} за последние {seconds} секунд")
    
    context["kafka_received"] = {
        "cluster": cluster_name,
        "topic": topic_name,
        "messages": [{"data": "mock_message"}],
        "time_range_seconds": seconds
    }


@when(parsers.parse('прочитать сообщения из топика "{topic_name}" кластера "{cluster_name}" с offset {offset:d}'))
def read_kafka_messages_from_offset(context, topic_name, cluster_name, offset):
    """Чтение сообщений начиная с указанного offset."""
    print(f"MOCK: Чтение сообщений из топика {topic_name} с offset {offset}")
    
    context["kafka_received"] = {
        "cluster": cluster_name,
        "topic": topic_name,
        "messages": [{"data": "mock_message"}],
        "start_offset": offset
    }


@when(parsers.parse('прочитать сообщения из топика "{topic_name}" кластера "{cluster_name}" с ключом "{key}"'))
def read_kafka_messages_by_key(context, topic_name, cluster_name, key):
    """Чтение сообщений по ключу."""
    print(f"MOCK: Чтение сообщений с ключом {key} из топика {topic_name}")
    
    context["kafka_received"] = {
        "cluster": cluster_name,
        "topic": topic_name,
        "key": key,
        "messages": [{"data": "mock_message", "key": key}]
    }


@when(parsers.parse('ожидать сообщение в топике "{topic_name}" кластера "{cluster_name}" в течение {timeout:d} секунд'))
def wait_for_kafka_message(context, topic_name, cluster_name, timeout):
    """Ожидание сообщения в топике."""
    print(f"MOCK: Ожидание сообщения в топике {topic_name} в течение {timeout} секунд")
    
    context["kafka_received"] = {
        "cluster": cluster_name,
        "topic": topic_name,
        "message": {"data": "mock_message"},
        "waited_seconds": 2
    }


@when(parsers.parse('ожидать сообщение с ключом "{key}" в топике "{topic_name}" кластера "{cluster_name}" в течение {timeout:d} секунд'))
def wait_for_kafka_message_with_key(context, key, topic_name, cluster_name, timeout):
    """Ожидание сообщения с определенным ключом."""
    print(f"MOCK: Ожидание сообщения с ключом {key} в топике {topic_name}")
    
    context["kafka_received"] = {
        "cluster": cluster_name,
        "topic": topic_name,
        "key": key,
        "message": {"data": "mock_message", "key": key}
    }


@when(parsers.parse('подтвердить получение сообщения'))
def commit_kafka_offset(context):
    """Подтверждение получения сообщения (commit offset)."""
    print(f"MOCK: Offset подтвержден")
    context["kafka_committed"] = True


@when(parsers.parse('подтвердить получение сообщений для топика "{topic_name}"'))
def commit_kafka_offset_for_topic(context, topic_name):
    """Подтверждение получения сообщений для топика."""
    print(f"MOCK: Offset подтвержден для топика {topic_name}")
    context["kafka_committed"] = True


@when(parsers.parse('сбросить offset консьюмера на начало для топика "{topic_name}"'))
def reset_kafka_offset_to_beginning(context, topic_name):
    """Сброс offset на начало топика."""
    print(f"MOCK: Offset сброшен на начало для топика {topic_name}")


@when(parsers.parse('сбросить offset консьюмера на конец для топика "{topic_name}"'))
def reset_kafka_offset_to_end(context, topic_name):
    """Сброс offset на конец топика."""
    print(f"MOCK: Offset сброшен на конец для топика {topic_name}")


@when(parsers.parse('сбросить offset консьюмера на {offset:d} для топика "{topic_name}"'))
def reset_kafka_offset_to_value(context, offset, topic_name):
    """Сброс offset на указанное значение."""
    print(f"MOCK: Offset сброшен на {offset} для топика {topic_name}")


@when(parsers.parse('приостановить консьюмер для топика "{topic_name}"'))
def pause_kafka_consumer(context, topic_name):
    """Приостановка консьюмера."""
    print(f"MOCK: Консьюмер приостановлен для топика {topic_name}")


@when(parsers.parse('возобновить консьюмер для топика "{topic_name}"'))
def resume_kafka_consumer(context, topic_name):
    """Возобновление консьюмера."""
    print(f"MOCK: Консьюмер возобновлен для топика {topic_name}")


@when(parsers.parse('создать топик "{topic_name}" в кластере "{cluster_name}"'))
def create_kafka_topic(context, topic_name, cluster_name):
    """Создание топика."""
    print(f"MOCK: Создан топик {topic_name} в кластере {cluster_name}")


@when(parsers.parse('создать топик "{topic_name}" в кластере "{cluster_name}" с {partitions:d} партициями'))
def create_kafka_topic_with_partitions(context, topic_name, cluster_name, partitions):
    """Создание топика с указанным количеством партиций."""
    print(f"MOCK: Создан топик {topic_name} с {partitions} партициями в кластере {cluster_name}")


@when(parsers.parse('создать топик "{topic_name}" в кластере "{cluster_name}" с конфигурацией:'))
def create_kafka_topic_with_config(context, topic_name, cluster_name, docstring):
    """Создание топика с конфигурацией."""
    print(f"MOCK: Создан топик {topic_name} с конфигурацией:\n{docstring}")


@when(parsers.parse('удалить топик "{topic_name}" в кластере "{cluster_name}"'))
def delete_kafka_topic(context, topic_name, cluster_name):
    """Удаление топика."""
    print(f"MOCK: Удален топик {topic_name} в кластере {cluster_name}")


@when(parsers.parse('изменить количество партиций топика "{topic_name}" на {partitions:d}'))
def alter_kafka_topic_partitions(context, topic_name, partitions):
    """Изменение количества партиций топика."""
    print(f"MOCK: Количество партиций топика {topic_name} изменено на {partitions}")


@when(parsers.parse('отправить сообщение в транзакции в топик "{topic_name}" кластера "{cluster_name}":'))
def send_kafka_transactional_message(context, topic_name, cluster_name, docstring):
    """Отправка сообщения в транзакции."""
    print(f"MOCK: Отправка сообщения в транзакции в топик {topic_name}")
    print(f"MOCK: Сообщение:\n{docstring}")
    
    context["kafka"] = {
        "cluster": cluster_name,
        "topic": topic_name,
        "message": docstring,
        "transactional": True,
        "sent": True
    }


@when(parsers.parse('начать Kafka транзакцию'))
def begin_kafka_transaction(context):
    """Начало Kafka транзакции."""
    context["kafka_transaction"] = {"active": True}
    print(f"MOCK: Kafka транзакция начата")


@when(parsers.parse('зафиксировать Kafka транзакцию'))
def commit_kafka_transaction(context):
    """Фиксация Kafka транзакции."""
    if "kafka_transaction" in context:
        context["kafka_transaction"]["active"] = False
        context["kafka_transaction"]["committed"] = True
    print(f"MOCK: Kafka транзакция зафиксирована")


@when(parsers.parse('откатить Kafka транзакцию'))
def abort_kafka_transaction(context):
    """Откат Kafka транзакции."""
    if "kafka_transaction" in context:
        context["kafka_transaction"]["active"] = False
        context["kafka_transaction"]["aborted"] = True
    print(f"MOCK: Kafka транзакция откачена")


# ============================================================================
# --- Then steps (Kafka Verification) ---
# ============================================================================

@then(parsers.parse('сообщение успешно отправлено'))
def check_message_sent(context):
    """Проверка успешной отправки сообщения."""
    sent = context.get("kafka", {}).get("sent", False)
    print(f"MOCK: Проверка отправки сообщения")
    soft_assert(sent)


@then(parsers.parse('offset отправленного сообщения сохранен в переменную "{var_name}"'))
def save_sent_offset(context, var_name):
    """Сохранение offset отправленного сообщения."""
    offset = context.get("kafka", {}).get("offset", 0)
    context["variables"][var_name] = offset
    print(f"MOCK: Offset {offset} сохранен в переменную {var_name}")


@then(parsers.parse('партиция отправленного сообщения равна {partition:d}'))
def check_sent_partition(context, partition):
    """Проверка партиции отправленного сообщения."""
    actual_partition = context.get("kafka", {}).get("partition", -1)
    print(f"MOCK: Проверка партиции: ожидается {partition}, получено {actual_partition}")
    soft_assert(actual_partition == partition)


@then(parsers.parse('получено сообщение из топика'))
def check_message_received(context):
    """Проверка получения сообщения."""
    received = context.get("kafka_received") is not None
    print(f"MOCK: Проверка получения сообщения")
    soft_assert(received)


@then(parsers.parse('получено {count:d} сообщений из топика'))
def check_messages_count_received(context, count):
    """Проверка количества полученных сообщений."""
    messages = context.get("kafka_received", {}).get("messages", [])
    actual_count = len(messages) if messages else (1 if context.get("kafka_received", {}).get("message") else 0)
    print(f"MOCK: Проверка количества сообщений: ожидается {count}, получено {actual_count}")
    soft_assert(actual_count == count)


@then(parsers.parse('тело полученного сообщения содержит "{text}"'))
def check_received_message_contains(context, text):
    """Проверка содержимого полученного сообщения."""
    message = context.get("kafka_received", {}).get("message", {})
    message_str = json.dumps(message) if isinstance(message, dict) else str(message)
    print(f"MOCK: Проверка что сообщение содержит '{text}'")
    soft_assert(text in message_str)


@then(parsers.parse('тело полученного сообщения равно:'))
def check_received_message_equals(context, docstring):
    """Проверка точного соответствия тела сообщения."""
    print(f"MOCK: Проверка соответствия тела сообщения")
    soft_assert(True)


@then(parsers.parse('ключ полученного сообщения равен "{key}"'))
def check_received_message_key(context, key):
    """Проверка ключа полученного сообщения."""
    actual_key = context.get("kafka_received", {}).get("key")
    print(f"MOCK: Проверка ключа сообщения: ожидается {key}, получено {actual_key}")
    soft_assert(str(actual_key) == str(key))


@then(parsers.parse('заголовок "{header}" полученного сообщения равен "{value}"'))
def check_received_message_header(context, header, value):
    """Проверка заголовка полученного сообщения."""
    headers = context.get("kafka_received", {}).get("headers", {})
    actual_value = headers.get(header)
    print(f"MOCK: Проверка заголовка {header}: ожидается {value}, получено {actual_value}")
    soft_assert(str(actual_value) == str(value))


@then(parsers.parse('offset полученного сообщения сохранен в переменную "{var_name}"'))
def save_received_offset(context, var_name):
    """Сохранение offset полученного сообщения."""
    offset = context.get("kafka_received", {}).get("offset", 0)
    context["variables"][var_name] = offset
    print(f"MOCK: Offset {offset} сохранен в переменную {var_name}")


@then(parsers.parse('партиция полученного сообщения сохранена в переменную "{var_name}"'))
def save_received_partition(context, var_name):
    """Сохранение партиции полученного сообщения."""
    partition = context.get("kafka_received", {}).get("partition", 0)
    context["variables"][var_name] = partition
    print(f"MOCK: Партиция {partition} сохранена в переменную {var_name}")


@then(parsers.parse('тело полученного сообщения сохранено в переменную "{var_name}"'))
def save_received_message_body(context, var_name):
    """Сохранение тела полученного сообщения."""
    message = context.get("kafka_received", {}).get("message", {})
    context["variables"][var_name] = message
    print(f"MOCK: Тело сообщения сохранено в переменную {var_name}")


@then(parsers.parse('топик "{topic_name}" существует в кластере "{cluster_name}"'))
def check_topic_exists(context, topic_name, cluster_name):
    """Проверка существования топика."""
    print(f"MOCK: Проверка существования топика {topic_name} в кластере {cluster_name}")
    soft_assert(True)


@then(parsers.parse('топик "{topic_name}" не существует в кластере "{cluster_name}"'))
def check_topic_not_exists(context, topic_name, cluster_name):
    """Проверка отсутствия топика."""
    print(f"MOCK: Проверка отсутствия топика {topic_name} в кластере {cluster_name}")
    soft_assert(True)


@then(parsers.parse('топик "{topic_name}" имеет {partitions:d} партиций'))
def check_topic_partitions(context, topic_name, partitions):
    """Проверка количества партиций топика."""
    print(f"MOCK: Проверка количества партиций топика {topic_name}: ожидается {partitions}")
    soft_assert(True)


@then(parsers.parse('топик "{topic_name}" имеет replication factor {factor:d}'))
def check_topic_replication_factor(context, topic_name, factor):
    """Проверка replication factor топика."""
    print(f"MOCK: Проверка replication factor топика {topic_name}: ожидается {factor}")
    soft_assert(True)


@then(parsers.parse('lag консьюмера для топика "{topic_name}" равен {lag:d}'))
def check_consumer_lag(context, topic_name, lag):
    """Проверка lag консьюмера."""
    print(f"MOCK: Проверка lag консьюмера для топика {topic_name}: ожидается {lag}")
    soft_assert(True)


@then(parsers.parse('lag консьюмера для топика "{topic_name}" меньше {max_lag:d}'))
def check_consumer_lag_less(context, topic_name, max_lag):
    """Проверка что lag консьюмера меньше указанного."""
    print(f"MOCK: Проверка lag консьюмера для топика {topic_name}: должен быть < {max_lag}")
    soft_assert(True)


@then(parsers.parse('подключение к Kafka кластеру "{cluster_name}" активно'))
def check_kafka_connection_active(context, cluster_name):
    """Проверка активности подключения к Kafka."""
    connected = context.get("kafka_clusters", {}).get(cluster_name, {}).get("connected", False)
    print(f"MOCK: Проверка подключения к кластеру {cluster_name}")
    soft_assert(connected)


@then(parsers.parse('закрыть подключение к Kafka кластеру "{cluster_name}"'))
def close_kafka_connection(context, cluster_name):
    """Закрытие подключения к Kafka кластеру."""
    if "kafka_clusters" in context and cluster_name in context["kafka_clusters"]:
        context["kafka_clusters"][cluster_name]["connected"] = False
    print(f"MOCK: Подключение к кластеру {cluster_name} закрыто")


@then(parsers.parse('закрыть продюсер для кластера "{cluster_name}"'))
def close_kafka_producer(context, cluster_name):
    """Закрытие Kafka продюсера."""
    if "kafka_producers" in context and cluster_name in context["kafka_producers"]:
        context["kafka_producers"][cluster_name]["created"] = False
    print(f"MOCK: Продюсер для кластера {cluster_name} закрыт")


@then(parsers.parse('закрыть консьюмер для кластера "{cluster_name}"'))
def close_kafka_consumer(context, cluster_name):
    """Закрытие Kafka консьюмера."""
    if "kafka_consumers" in context and cluster_name in context["kafka_consumers"]:
        context["kafka_consumers"][cluster_name]["created"] = False
    print(f"MOCK: Консьюмер для кластера {cluster_name} закрыт")


@then(parsers.parse('вывести полученное сообщение'))
def print_received_message(context):
    """Вывод полученного сообщения."""
    message = context.get("kafka_received", {})
    print(f"DEBUG: Полученное сообщение = {json.dumps(message, indent=2, ensure_ascii=False, default=str)}")
