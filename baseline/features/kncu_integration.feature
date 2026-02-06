Feature: Kncu Integration

  @rest @typeA
  Scenario: Проверка корректности обработки запроса типа A внешним сервисом
    Given настроен REST клиент для сервера "external-integration"
    When присвоить переменной "correlationId" случайную строку длиной 36
    When Отправить "/execute" на REST сервер "external-integration" с body из файла "type_a_req.json"
    Then Проверить ответ с кодом 200
    And сравнить ответ с эталоном из файла "type_a_res.json"

  @rest @typeB
  Scenario: Проверка корректности обработки запроса типа B внешним сервисом
    Given настроен REST клиент для сервера "external-integration"
    When присвоить переменной "correlationId" случайную строку длиной 36
    When Отправить "/execute" на REST сервер "external-integration" с body из файла "type_b_req.json"
    Then Проверить ответ с кодом 200
    And сравнить ответ с эталоном из файла "type_b_res.json"

  @rest @typeC
  Scenario: Проверка корректности обработки запроса типа C внешним сервисом
    Given настроен REST клиент для сервера "external-integration"
    When присвоить переменной "correlationId" случайную строку длиной 36
    When Отправить "/execute" на REST сервер "external-integration" с body из файла "type_c_req.json"
    Then Проверить ответ с кодом 200
    And сравнить ответ с эталоном из файла "type_c_res.json"
