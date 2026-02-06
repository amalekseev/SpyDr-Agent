Feature: Guarantee Margin

  @restapi @db @margin
  Scenario: Расчет маржи через сервис расчетов
    Given настроен REST клиент для сервера "calc_service"
    Given установлен API ключ "test-api-key" для сервера "calc_service"
    Given подготовлен тестовый контекст
    Given установлено подключение к базе данных "postgres_dev"
    When присвоить переменной "requestId" случайную строку длиной 16
    When установить переменную "calcId" значением "CALC-00001"
    When Отправить "/api/v1/margin" на REST сервер "calc_service" с body из файла "margin_req.json"
    Then код ответа сервера "calc_service" равен 200
    Then сравнить ответ с эталоном из файла "margin_res.json"
    When выполнить SELECT запрос в базу "postgres_dev":
      """
      SELECT count(*) FROM APP_SCHEMA.CALC_SERVICE WHERE request_id = '{requestId}'
      """
    Then результат запроса в базу "postgres_dev" содержит данные в течение 60 секунд
    Then результат запроса содержит 1 строк
