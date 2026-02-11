Feature: Hierarchy Covenants

  Scenario: Проверка расчета ставки калькулятором Calc
    Given установлен идентификатор запроса "traceId"
    When установить переменную "enableFeature" значением "No"
    When отправить POST запрос на сервер "calc_hierarchy_service" endpoint "/calc?calculatorName=Calc" с телом:
      """
      {
        "file": "calc_request.json"
      }
      """
    Then Проверить ответ с кодом 200
    Then тело ответа содержит поле "traceId" со значением "traceId"
    Then сохранить значение поля "rateAdjustment" из ответа в переменную "rateAdjustmentValue"
    Then отображается сообщение об ошибке авторизации
