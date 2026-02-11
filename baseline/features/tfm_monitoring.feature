Feature: Tfm Monitoring

  Scenario: Проверка статистики сервиса
    When отправить GET запрос на сервер "app_service" endpoint "/service/monitoring/statistics"
    Then Проверить ответ с кодом 200
    Then тело ответа является валидным JSON

  Scenario: Проверка загрузки данных из внешнего источника
    Given очищена таблица "APP_SCHEMA.ACCOUNT_BALANCE" в базе "postgres"
    When Отправить сообщение в кафку "kafka_app" в топик "APP-TOPIC-ACCOUNTBALANCE" из файла "record timestamp='2023-01-01T10:00:00.000' exchange='EXCHANGE' market='MKT' system='SYS' entity='ENTITY' interface='API' table='ACCOUNT_BALANCE' POSITION_ID='00001' /"
    When выполнить SELECT запрос в базу "postgres":
      """
      Выполнить SELECT запрос.
      """
    Then результат запроса в базу "postgres" содержит данные в течение 60 секунд
