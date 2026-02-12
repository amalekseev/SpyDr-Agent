Feature: Acquiring Tariffs

  Scenario: Проверка всех тарифов
    Given установлен идентификатор запроса "уникальный идентификатор запроса"
    Given установлен формат даты "yyyy-MM-ddTHH:mm:ss"
    Given установлен идентификатор пользователя "urn:mock:autotest, urn:mock:system"
    When Отправить "POST /mock-gateway/v1/tariffs/recommended" на REST сервер "rest_mock" с хедерами "rqUid: уникальный идентификатор запроса, rqTm: текущая дата и время, spName: urn:mock:autotest, systemId: urn:mock:system" с body из файла "request_recommended.json"
    Then Проверить ответ с кодом 200 и body из файла "response_recommended.json"
    Given установлен идентификатор запроса "новый UUID для идентификатора запроса расчета"
    Given установлен идентификатор клиента "уникальный номер контракта"
    Given включено логирование запросов
    When Отправить "POST /mock-gateway/v1/calculation/profitability" на REST сервер "rest_mock" с хедерами "rqUid: идентификатор запроса расчета, rqTm: текущее время, spName: urn:mock:autotest, systemId: urn:mock:system" с body из файла "request_profitability.json"
    Then код ответа должен быть 200
    Then заголовок ответа "rquid" существует
    When отправить GET запрос на сервер "rest_mock" endpoint "/mock-gateway/v1/reports/by-uid"
    Then Проверить ответ с кодом 200 и body
      """
      Проверка успешного ответа с кодом 200.
      """
    Then тело полученного сообщения равно:
      """
      Проверка точного соответствия тела сообщения сообществу.
      """
    When отправить GET запрос на сервер "rest_mock" endpoint "/mock-gateway/v1/reports/by-id"
    When повторить последний запрос на сервер "rest_mock" 60 раз
    Then размер ответа больше 2048 байт
    Given установлен формат даты "первый день текущего месяца плюс 1 год"
    Then результат запроса в первой строке содержит "0.025" в колонке "payback_1year"
    Then результат запроса в первой строке содержит "0.018" в колонке "payback_3year"
    Then результат запроса в первой строке содержит "max(payback_1year, 0.02)" в колонке "рекомендованный тариф"
