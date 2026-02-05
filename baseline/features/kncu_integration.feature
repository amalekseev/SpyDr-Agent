Feature: Kncu Integration

  @integration
  Scenario: Тест на интеграцию с внешним сервисом для типа "type_a"
    Given подготовлен тестовый контекст
    When присвоить переменной "correlationId" случайную строку длиной 36
    When отправить POST запрос на сервер "external-integration" endpoint "/execute" с телом из файла "type_a_req.json"
    Then код ответа должен быть 200
    Then сравнить ответ с эталоном из файла "type_a_res.json"

  @integration
  Scenario: Тест на интеграцию с внешним сервисом для типа "type_b"
    Given подготовлен тестовый контекст
    When присвоить переменной "correlationId" случайную строку длиной 36
    When отправить POST запрос на сервер "external-integration" endpoint "/execute" с телом из файла "type_b_req.json"
    Then код ответа должен быть 200
    Then сравнить ответ с эталоном из файла "type_b_res.json"

  @integration
  Scenario: Тест на интеграцию с внешним сервисом для типа "type_c"
    Given подготовлен тестовый контекст
    When присвоить переменной "correlationId" случайную строку длиной 36
    When отправить POST запрос на сервер "external-integration" endpoint "/execute" с телом из файла "type_c_req.json"
    Then код ответа должен быть 200
    Then сравнить ответ с эталоном из файла "type_c_res.json"
