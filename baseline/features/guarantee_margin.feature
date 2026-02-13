Feature: Guarantee Margin

  Scenario: Расчет маржи через сервис расчетов
    Given установлен идентификатор запроса "requestId"
    Given установлен идентификатор клиента "CALC-00001"
    When Отправить "/api/v1/margin" на REST сервер "calc_service" с body из файла "margin_req.json"
    Then Проверить ответ с кодом 200 и body из файла "margin_res.json"
    When выполнить SELECT запрос в базу "postgres_dev":
      """
      SELECT count(*) FROM APP_SCHEMA.CALC_SERVICE WHERE request_id = '
      """
    Then результат запроса в базу "postgres_dev" содержит данные в течение 60 секунд
