Feature: Tfm Monitoring

  @api @monitoring @statistics
  Scenario: Проверка статистики сервиса
    When отправить GET запрос на сервер "app_service" endpoint "/service/monitoring/statistics"
    Then код ответа сервера "app_service" равен 200
    And ответ содержит JSON поле "actionTasks"
    And ответ содержит вложенное поле "actionTasks.TaskRegenerate"
    And ответ содержит вложенное поле "actionTasks.TaskRegenerate.waitingCount" типа "integer"

  @db @kafka @integration
  Scenario: Проверка загрузки данных из внешнего источника
    Given установлено подключение к базе данных "postgres"
    When выполнить SQL запрос в базу "postgres":
      """
      DELETE FROM APP_SCHEMA.ACCOUNT_BALANCE WHERE POSITION_ID = '00001'
      """
    Then закрыть подключение к базе "postgres"
    When Отправить сообщение в кафку "kafka_app" в топик "APP-TOPIC-ACCOUNTBALANCE"
    Then сообщение успешно отправлено
    Given установлено подключение к базе данных "postgres"
    When выполнить SELECT запрос в базу "postgres":
      """
      SELECT * FROM APP_SCHEMA.ACCOUNT_BALANCE WHERE POSITION_ID = '00001'
      """
    Then Проверить результат запроса из базы "postgres" в течение 60 секунд
    And результат запроса в первой строке содержит "00001" в колонке "POSITION_ID"
    And закрыть подключение к базе "postgres"
