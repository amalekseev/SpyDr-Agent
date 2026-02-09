Feature: Guarantee Margin

  @api @db @margin
  Scenario: Расчет маржи через сервис расчетов
    Given настроен REST клиент для сервера "calc_service"
    Given установлен API ключ "test-key" для сервера "calc_service"
    Given установлено подключение к базе данных "postgres_dev"
    When присвоить переменной "requestId" случайную строку длиной 16
    When присвоить переменной "calcId" значение "CALC-00001"
    When Отправить "/api/v1/margin" на REST сервер "calc_service" с body из файла "margin_req.json"
    Then Проверить ответ с кодом 200 и body из файла "margin_res.json"
    When выполнить SELECT запрос в базу "postgres_dev":
      """
      SELECT count(*) FROM APP_SCHEMA.CALC_SERVICE WHERE request_id = '{requestId}'
      """
    Then результат запроса в базу "postgres_dev" содержит данные в течение 60 секунд
    Then результат запроса содержит 1 строк
