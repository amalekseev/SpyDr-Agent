Feature: Kncu Integration

  Scenario: Проверка корректности обработки запроса типа A внешним сервисом
    Given установлен идентификатор корреляции "UUID"
    When Отправить "POST /execute" на REST сервер "external-integration" с body из файла "type_a_req.json"
    Then тест завершен успешно

  Scenario: Проверка корректности обработки запроса типа B внешним сервисом
    Given установлен идентификатор корреляции "UUID"
    When Отправить "POST /execute" на REST сервер "external-integration" с body из файла "type_b_req.json"
    Then тест завершен успешно

  Scenario: Проверка корректности обработки запроса типа C внешним сервисом
    Given установлен идентификатор корреляции "UUID"
    When Отправить "POST /execute" на REST сервер "external-integration" с body из файла "type_c_req.json"
    Then тест завершен успешно
