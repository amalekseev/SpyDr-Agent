Feature: Hierarchy Covenants

  Scenario: Проверка расчета ставки калькулятором Calc
    Given установлен идентификатор запроса "traceId"
    Given установлен идентификатор сессии "No"
    When отправить POST запрос на сервер "calc_hierarchy_service" endpoint "/calc?calculatorName=Calc" с телом:
      """
      {
        "file": "calc_request.json"
      }
      """
    Then код ответа сервера "calc_hierarchy_service" равен 200
    Then тело ответа содержит поле "traceId" со значением не равным "traceId"
    Then тело ответа содержит поле "outAttributes.rateAdjustment"
    Then вывести полученное сообщение
