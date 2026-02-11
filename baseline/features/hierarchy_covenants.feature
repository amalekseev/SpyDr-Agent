Feature: Hierarchy Covenants

  Scenario: Проверка расчета ставки калькулятором Calc
    Given установлен идентификатор запроса "traceId"
    Given установлен идентификатор запроса "enableFeature=No"
    When Отправить "POST /calc?calculatorName=Calc" на REST сервер "calc_hierarchy_service" с body из файла "calc_request.json"
    Then код ответа сервера "calc_hierarchy_service" равен 200
    Then тело ответа содержит поле "traceId" со значением "traceId"
    Then тело ответа содержит поле "outAttributes.rateAdjustment"
    Then вывести полученное сообщение
