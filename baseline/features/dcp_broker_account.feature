@dcp_broker_account
Feature: Dcp Broker Account

  @account_creation @account_closure
  Scenario: Загрузка нового счета и его отмена
    When Отправить сообщение в кафку "kafka_mock" в топик "MOCK-INCOMING-ACCOUNT" из файла "data/kafka_templates/mock_account.xml"
    Then результат запроса в базу "postgres_mock_raw" содержит данные в течение 120 секунд
    Then результат запроса содержит данные:
    Then ID вставленной записи сохранен в переменную "recordIdFirst"
    Then таблица "mock_raw.raw_internal_account_agreement" содержит 2 строк
    Then таблица "mock_main.contract" в базе "postgres_mock_main" содержит 2 записей
    Then таблица "mock_main.account" в базе "postgres_mock_main" содержит 1 записей
    Given отключены всплывающие окна
    When Отправить сообщение в кафку "kafka_mock" в топик "MOCK-INCOMING-ACCOUNT" из файла "data/kafka_templates/mock_account.xml"
    Then результат запроса в базу "postgres_mock_raw" содержит данные в течение 120 секунд
    Then результат запроса содержит данные:
    Then ID вставленной записи сохранен в переменную "recordIdSecond"
    Then таблица "mock_raw.raw_internal_account_agreement" содержит 2 строк
    Then таблица "mock_main.contract" в базе "postgres_mock_main" содержит 2 записей
    Then таблица "mock_main.account" в базе "postgres_mock_main" содержит 1 записей
