Feature: Tfm Monitoring

  Scenario: Проверка статистики сервиса
    When отправить GET запрос на сервер "app_service" endpoint "/service/monitoring/statistics"
    Then Проверить ответ с кодом 200
    Then тело ответа содержит массив "actionTasks.TaskRegenerate.waitingCount" с количеством элементов меньше 0

  Scenario: Проверка загрузки данных из внешнего источника
    Given очищена таблица "APP_SCHEMA.ACCOUNT_BALANCE" в базе "postgres"
    When отправить сообщение в транзакции в топик "APP-TOPIC-ACCOUNTBALANCE" кластера "kafka_app":
      """
      <record timestamp='2023-01-01T10:00:00.000' exchange='EXCHANGE' market='MKT' system='SYS' entity='ENTITY' interface='API' table='ACCOUNT_BALANCE' POSITION_ID='00001' />
      """
    When выполнить SELECT запрос в базу "postgres":
      """
      SELECT * FROM APP_SCHEMA.ACCOUNT_BALANCE WHERE POSITION_ID = '00001'
      """
    Then результат запроса в базу "postgres" содержит данные в течение 60 секунд
