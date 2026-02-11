@guarantee_margin
Feature: Guarantee Margin

  @margin_calculation
  Scenario: Расчет маржи через сервис расчетов
    Given установлен идентификатор запроса "requestId"
    Given установлен идентификатор клиента "CALC-00001"
    When Отправить "POST /api/v1/margin" на REST сервер "calc_service" с body из файла "margin_req.json"
    Then код ответа сервера "calc_service" равен 200
    Then Проверить ответ с кодом 200 в течение 60 секунд
    When выполнить SQL запрос в базу "postgres_dev":
      """
      SELECT count(*) FROM APP_SCHEMA.CALC_SERVICE WHERE request_id = '<requestId>'.
      """
    Then таблица "APP_SCHEMA.CALC_SERVICE" в базе "postgres_dev" содержит 1 записей
    Then время выполнения запроса меньше 60 секунд
