Feature: Tfm Monitoring

  Scenario: Проверка статистики сервиса
    When отправить GET запрос на сервер "app_service" endpoint "/service/monitoring/statistics"
    Then Проверить ответ с кодом 200
    Then ответ содержит JSON массив "actionTasks.TaskRegenerate.waitingCount" с 1 элементами

  Scenario: Проверка загрузки данных из внешнего источника
    When выполнить DELETE запрос в базу "postgres":
      """
      DELETE FROM APP_SCHEMA.ACCOUNT_BALANCE WHERE POSITION_ID = '00001'
      """
    When Отправить сообщение в кафку "kafka_app" в топик "APP-TOPIC-ACCOUNTBALANCE" из файла "message.xml"
    When выполнить SELECT запрос в базу "postgres":
      """
      SELECT * FROM APP_SCHEMA.ACCOUNT_BALANCE WHERE POSITION_ID = '00001'
      """
    Then результат запроса в базу "postgres" содержит данные в течение 60 секунд
