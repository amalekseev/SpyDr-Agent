@margin_calc
Feature: Расчет маржи

  Scenario: Расчет маржи через сервис расчетов
    When Присвоить переменной "requestId" значение "${UUID}"
    And Присвоить переменной "calcId" значение "CALC-00001"
    And Отправить "POST /api/v1/margin" на REST сервер "calc_service" с body из файла "requests/margin_req.json"
    Then Проверить ответ с кодом 200 и body из файла "responses/margin_res.json"
    
    When Комментарий "Проверка записи в БД"
    And выполнить SQL запрос в базу "postgres_dev":
      """sql
      SELECT count(*) FROM APP_SCHEMA.CALC_SERVICE WHERE request_id = '${requestId}'
      """
    Then результат запроса в базу "postgres_dev" содержит данные в течение 60 секунд
      | count(*) |
      | 1        |
