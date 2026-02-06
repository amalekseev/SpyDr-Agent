Feature: Hierarchy Covenants

  @api @calculation
  Scenario: Проверка расчета ставки калькулятором Calc
    Given настроен REST клиент для сервера "calc_hierarchy_service"
    When присвоить переменной "traceId" случайную строку длиной 32
    When установить переменную "enableFeature" значением "No"
    When Отправить "POST /calc?calculatorName=Calc" на REST сервер "calc_hierarchy_service" с body из файла "calc_request.json"
    Then код ответа сервера "calc_hierarchy_service" равен 200
    Then ответ содержит JSON поле "traceId" со значением "{traceId}"
    Then ответ содержит JSON массив "outAttributes" с элементом где "name" равен "rateAdjustment"
    Then сохранить значение вложенного поля "$.outAttributes[?(@.name=='rateAdjustment')].value" из ответа в переменную "rateAdjustment"
    When добавить заметку "Проверка бизнес-логики расчета"
    Then тест завершен успешно
