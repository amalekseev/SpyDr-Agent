@api @calc @hierarchy
Feature: Hierarchy Covenants

  Scenario: Расчет ставки в системе
    When присвоить переменной "traceId" случайную строку длиной 36
    And установить переменную "enableFeature" значением "No"
    When Отправить "POST /calc?calculatorName=Calc" на REST сервер "calc_hierarchy_service" с body из файла "calc_request.json"
    Then код ответа сервера "calc_hierarchy_service" равен 200
    And ответ является валидным JSON
    And ответ содержит JSON поле "dont_check_array_len" со значением "true"
    And ответ содержит JSON массив "outAttributes" с элементом где "rateAdjustment" равен "${rateAdjustment_1}"
    And ответ содержит JSON поле "traceId"
    And сохранить значение поля "traceId" из ответа в переменную "traceId_response"
    And переменная "traceId_response" равна "${traceId}"
    Then Выполнить python код
