@hierarchy
Feature: Иерархия и расчеты

  Scenario: Проверка расчета ставки
    When Присвоить переменной "traceId" значение "${UUID}"
    And Присвоить переменной "enableFeature" значение "No"
    And Отправить "POST /calc?calculatorName=Calc" на REST сервер "calc_hierarchy_service" с body из файла "calc_request.json"
    Then Проверить ответ с кодом 200 и body
      """json
      {
        "dont_check_array_len": true,
        "outAttributes": {
           "rateAdjustment": "${rateAdjustment_1}"
           },
        "traceId": "${traceId}"
      }
      """
    And Выполнить python код
      """py
      print("Проверка бизнес-логики расчета")
      """
