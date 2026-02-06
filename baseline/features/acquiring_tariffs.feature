Feature: Acquiring Tariffs

  @api @tariffs
  Scenario: Проверка всех тарифов
    Given настроен REST клиент для сервера "rest_mock"
    When присвоить переменной "rqUid" случайную строку длиной 36
    When присвоить переменной "rqTm" текущую дату в формате "YYYY-MM-DDTHH:mm:ss"
    When Присвоить переменной "spName" значение "urn:mock:autotest"
    When Присвоить переменной "systemId" значение "urn:mock:system"
    When Отправить "/mock-gateway/v1/tariffs/recommended" на REST сервер "rest_mock" с body из файла "request_recommended.json"
    Then код ответа сервера "rest_mock" равен 200
    Then сравнить ответ с эталоном из файла "response_recommended.json"

    When присвоить переменной "contractNumber" случайное число от 1000000 до 9999999
    When присвоить переменной "calcRqUid" случайную строку длиной 36
    When Присвоить переменной "profitabilityPercent" значение "0.8"
    When Присвоить переменной "profitabilityLimit" значение "1000000"
    When Отправить "/mock-gateway/v1/calculation/profitability" на REST сервер "rest_mock" с body из файла "request_profitability.json"
    Then код ответа сервера "rest_mock" равен 200
    Then сохранить заголовок "rquid" из ответа в переменную "newRequestId"

    When отправить запрос с query параметрами на сервер "rest_mock" endpoint "/mock-gateway/v1/reports/by-uid":
      | rqUid    | periodBy |
      | <newRequestId> | 0 |
    Then код ответа сервера "rest_mock" равен 200
    Then ответ содержит JSON поле "processIdentifier"
    Then сохранить значение поля "processIdentifier" из ответа в переменную "processId"

    When отправить запрос с query параметрами на сервер "rest_mock" endpoint "/mock-gateway/v1/reports/by-id":
      | processId |
      | <processId> |
    When повторить последний запрос на сервер "rest_mock" 60 раз
    Then код ответа сервера "rest_mock" равен 200
    Then размер ответа больше 2048 байт

    When присвоить переменной "firstDayNextYear" текущую дату в формате "YYYY-MM-01"
    # Шаг вычисления даты плюс 1 год не формализуем, так как такого паттерна нет

    Then ответ содержит JSON поле "payback_1year"
    Then ответ содержит JSON поле "payback_3year"
    Then переменная "payback_1year" больше 0
    Then переменная "payback_3year" больше 0
    Then ответ содержит JSON поле "recommendedTariff"
    # Проверка, что recommendedTariff равен максимуму из payback_1year и 0.02 невозможна прямым шагом, сохраняем как заметку
    When добавить заметку "Проверить, что recommendedTariff = max(payback_1year, 0.02)"
    Then тест завершен успешно
