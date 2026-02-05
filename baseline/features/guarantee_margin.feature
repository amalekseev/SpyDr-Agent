Feature: Guarantee Margin

Scenario: Расчет маржи через сервис расчетов
  Given подготовлен тестовый контекст
  When присвоить переменной "requestId" случайную строку длиной 36
  When присвоить переменной "calcId" значением "CALC-00001"
  When Отправить "/api/v1/margin" на REST сервер "calc_service" с body из файла "requests/margin_req.json"
  Then Проверить ответ с кодом 200 и body из файла "responses/margin_res.json"
  When выполнить SELECT запрос в базу "postgres_dev":
    """
    SELECT count(*) FROM APP_SCHEMA.CALC_SERVICE WHERE request_id = '${requestId}'
    """
  Then результат запроса в базу "postgres_dev" содержит данные в течение 60 секунд
  Then результат запроса содержит значение "1" в колонке "count"
