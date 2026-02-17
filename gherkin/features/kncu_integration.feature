@integration
Feature: Интеграция с внешним сервисом

  Scenario Outline: Проверка маппинга для различных типов
    When Присвоить переменной "correlationId" значение "${UUID}"
    And Отправить "POST /execute" на REST сервер "external-integration" с body из файла "<request>"
    Then Проверить ответ с кодом 200 и body из файла "<response>"

    Examples:
      | name   | request           | response           |
      | type_a | type_a_req.json   | type_a_res.json    |
      | type_b | type_b_req.json   | type_b_res.json    |
      | type_c | type_c_req.json   | type_c_res.json    |
