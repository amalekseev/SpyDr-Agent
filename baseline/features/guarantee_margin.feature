@guarantee_margin
Feature: Guarantee Margin

  @margin_calculation
  Scenario: Расчет маржи через сервис расчетов
    Given установлен идентификатор запроса "requestId"
    Given установлен идентификатор запроса "CALC-00001"
    When отправить POST запрос на сервер "calc_service" endpoint "/api/v1/margin" с телом:
      """
      {
        "file": "margin_req.json"
      }
      """
    Then ответ является валидным JSON
    Then результат запроса содержит 1 строк
    Then результат запроса в базу "postgres_dev" содержит данные в течение 60 секунд
