@integration @external
Feature: Kncu Integration

  Scenario: Интеграция с внешним сервисом для типа "type_a"
    Given настроен REST клиент для сервера "external-integration"
    When Присвоить переменной "correlationId" значение "UUID"
    And Отправить "POST /execute" на REST сервер "external-integration" с body из файла "type_a_req.json"
    Then код ответа сервера "external-integration" равен 200
    And сравнить ответ с эталоном из файла "type_a_res.json"

  Scenario: Интеграция с внешним сервисом для типа "type_b"
    Given настроен REST клиент для сервера "external-integration"
    When Присвоить переменной "correlationId" значение "UUID"
    And Отправить "POST /execute" на REST сервер "external-integration" с body из файла "type_b_req.json"
    Then код ответа сервера "external-integration" равен 200
    And сравнить ответ с эталоном из файла "type_b_res.json"

  Scenario: Интеграция с внешним сервисом для типа "type_c"
    Given настроен REST клиент для сервера "external-integration"
    When Присвоить переменной "correlationId" значение "UUID"
    And Отправить "POST /execute" на REST сервер "external-integration" с body из файла "type_c_req.json"
    Then код ответа сервера "external-integration" равен 200
    And сравнить ответ с эталоном из файла "type_c_res.json"
