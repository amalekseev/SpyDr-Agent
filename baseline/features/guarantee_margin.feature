@api @db @margin @calc_service
Feature: Guarantee Margin

  Scenario: Расчет маржи через сервис расчетов
    Given подготовлен тестовый контекст
    When присвоить переменной "requestId" случайную строку длиной 36
    And Присвоить переменной "calcId" значение "CALC-00001"
    And Отправить "POST /api/v1/margin" на REST сервер "calc_service" с body из файла "requests/margin_req.json"
    Then Проверить ответ с кодом 200 и body из файла "responses/margin_res.json"
    When выполнить SQL запрос в базу "postgres_dev":
      """
      SELECT count(*) FROM APP_SCHEMA.CALC_SERVICE WHERE request_id = '${requestId}'
      """
    Then Проверить результат запроса из базы "postgres_dev" в течение 60 секунд
    And результат запроса содержит 1 строк
    And результат запроса в первой строке содержит "1" в колонке "count(*)"
