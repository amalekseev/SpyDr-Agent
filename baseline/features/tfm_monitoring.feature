Feature: Tfm Monitoring

  Scenario: Проверка статистики сервиса
    Given включено логирование запросов для сервера "app_service"
    When отправить GET запрос на сервер "app_service" endpoint "/service/monitoring/statistics"
    Then Проверить ответ с кодом 200
    Then ответ содержит JSON поле "actionTasks"
    Then ответ содержит JSON поле "TaskRegenerate"
    Then ответ содержит JSON поле "waitingCount"

  Scenario: Проверка загрузки данных из внешнего источника
    Given очищена таблица "ACCOUNT_BALANCE" в базе "postgres"
    When Отправить сообщение в кафку "kafka_app" в топик "APP-TOPIC-ACCOUNTBALANCE"
    When выполнить SELECT запрос в базу "postgres":
      """
      SELECT * FROM APP_SCHEMA.ACCOUNT_BALANCE WHERE POSITION_ID = '00001';
      """
    Then результат запроса в базу "postgres" содержит данные в течение 60 секунд
