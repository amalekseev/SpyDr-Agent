Feature: Hierarchy Covenants

  Scenario: Проверка расчета ставки калькулятором Calc
    Given установлен идентификатор запроса "traceId"
    Given установлен идентификатор клиента "enableFeature=No"
    When Отправить "POST /calc?calculatorName=Calc" на REST сервер "calc_hierarchy_service" с body из файла "calc_request.json"
    Then Проверить ответ с кодом 200
    Then ответ содержит JSON поле "traceId" со значением "traceId"
    Then ключ полученного сообщения равен "rateAdjustment"
    Then вывести полученное сообщение
