Feature: Guarantee Margin

  Scenario: Расчет маржи через сервис расчетов
    Given установлен идентификатор запроса "requestId"
    Given установлен идентификатор клиента "CALC-00001"
    When отправить POST запрос на сервер "calc_service" endpoint "/api/v1/margin" с телом:
      """
      {
        "file": "margin_req.json"
      }
      """
    Then Проверить ответ с кодом 200 и body из файла "margin_res.json"
    Then результат запроса содержит 1 строк
    When повторить последний запрос
    Then результат запроса в базу "postgres_dev" содержит данные в течение 60 секунд
