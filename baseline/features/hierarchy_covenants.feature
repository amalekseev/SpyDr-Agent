Feature: Hierarchy Covenants

Scenario: Проверка расчета ставки в системе
    Given подготовлен тестовый контекст
    When присвоить переменной "traceId" случайную строку длиной 36
    When установить переменную "enableFeature" значением "No"
    When Отправить "/calc" на REST сервер "calc_hierarchy_service" с body из файла "calc_request.json"
    Then код ответа сервера "calc_hierarchy_service" равен 200
    Then тело ответа содержит поле "dont_check_array_len" со значением "true"
    Then ответ содержит JSON массив "outAttributes" с элементом где "rateAdjustment" равен "${rateAdjustment_1}"
    Then переменная "traceId" равна "${traceId}"
    Then Выполнить python код
