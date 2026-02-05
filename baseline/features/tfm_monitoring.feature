Feature: Tfm Monitoring

Scenario: Проверка статистики сервиса
  Given настроен REST клиент для сервера "app_service"
  When отправить GET запрос на сервер "app_service" endpoint "/service/monitoring/statistics"
  Then код ответа сервера "app_service" равен 200
  Then ответ является валидным JSON
  Then ответ содержит JSON поле "actionTasks"
  Then ответ содержит вложенное поле "actionTasks.TaskRegenerate"
  Then ответ содержит вложенное поле "actionTasks.TaskRegenerate.waitingCount" типа "integer"

Scenario: Проверка загрузки данных из внешнего источника
  Given установлено подключение к базе данных "postgres"
  When выполнить DELETE запрос в базу "postgres":
    """
    DELETE FROM APP_SCHEMA.ACCOUNT_BALANCE WHERE POSITION_ID = '00001'
    """
  When отправить XML запрос на сервер "kafka_app" endpoint "APP-TOPIC-ACCOUNTBALANCE":
    """
    <record POSITION_ID='00001'/>
    """
  Given установлено подключение к базе данных "postgres"
  When выполнить SELECT запрос в базу "postgres":
    """
    SELECT * FROM APP_SCHEMA.ACCOUNT_BALANCE WHERE POSITION_ID = '00001'
    """
  Then результат запроса в базу "postgres" содержит данные в течение 60 секунд
