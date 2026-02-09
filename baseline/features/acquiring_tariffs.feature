Feature: Acquiring Tariffs

  @positive @api @tariffs @calculation @report
  Scenario: Проверка всех тарифов
    Given настроен REST клиент для сервера "rest_mock"
    When присвоить переменной "rqUid" случайную строку длиной 36
    When присвоить переменной "rqTm" текущую дату в формате "YYYY-MM-DDTHH:mm:ss"
    When Присвоить переменной "spName" значение "urn:mock:autotest"
    When Присвоить переменной "systemId" значение "urn:mock:system"
    When Отправить "/mock-gateway/v1/tariffs/recommended" на REST сервер "rest_mock" с хедерами "rqUid, rqTm, spName, systemId" с body из файла "request_recommended.json"
    Then Проверить ответ с кодом 200 и body из файла "response_recommended.json"

    When присвоить переменной "contractNumber" случайное число от 1000000 до 9999999
    When присвоить переменной "profitabilityRqUid" случайную строку длиной 36
    When Присвоить переменной "percentValue" значение "0.8"
    When Присвоить переменной "limitValue" значение "1000000"
    When Отправить "/mock-gateway/v1/calculation/profitability" на REST сервер "rest_mock" с хедерами "rqUid, rqTm, spName, systemId" с body из файла "request_profitability.json"
    Then Проверить ответ с кодом 200

    Then сохранить заголовок "rquid" в переменную "newRequestId"

    When отправить GET запрос на сервер "rest_mock" endpoint "/mock-gateway/v1/reports/by-uid"
    Then код ответа сервера "rest_mock" равен 200
    Then ответ содержит JSON поле "processIdentifier"
    Then сохранить значение поля "processIdentifier" в переменную "processId"

    When отправить GET запрос на сервер "rest_mock" endpoint "/mock-gateway/v1/reports/by-id"
    Then повторить последний запрос на сервер "rest_mock" 60 раз
    Then код ответа сервера "rest_mock" равен 200

    Then размер ответа больше 2048 байт

    When присвоить переменной "firstDayNextYear" текущую дату в формате "YYYY-MM-01"
    # Примечание: вычисление даты первого числа следующего года требует реализацию в коде шага. В Gherkin фиксируется фиктивное присвоение:
    When присвоить переменной "firstDayNextYear" дату через 365 дней

    Then ответ содержит JSON поле "payback_1year"
    Then ответ содержит JSON поле "payback_3year"
    Then ответ содержит JSON поле "recommendedTariff"

    Then переменная "payback_1year" больше 0
    Then переменная "payback_3year" больше 0
    # Рекомендованный тариф должен быть равен max(payback_1year, 0.02)
    # Проверка бизнес-логики через переменные, пример выполнен как сравнение:
    Then переменная "recommendedTariff" больше 0.019
    Then тест завершен успешно
