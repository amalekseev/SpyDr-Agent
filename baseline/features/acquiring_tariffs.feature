@acquiring @tariffs
Feature: Acquiring Tariffs

  @check_all_tariffs
  Scenario: Проверка всех тарифов
    Given установлен идентификатор запроса "уникальный UUID для запроса"
    Given установлен формат даты "yyyy-MM-ddTHH:mm:ss"
    Given установлен идентификатор запроса "spName=urn:mock:autotest, systemId=urn:mock:system"
    When Отправить "POST /mock-gateway/v1/tariffs/recommended" на REST сервер "rest_mock" с хедерами "{"rqUid":"уникальный UUID для запроса","rqTm":"текущая дата и время","spName":"urn:mock:autotest","systemId":"urn:mock:system"}" с body из файла "request_recommended.json"
    Then код ответа сервера "rest_mock" равен 200
    Then ответ соответствует JSON схеме из файла "response_recommended.json"
    Given установлен идентификатор запроса "новый UUID для запроса расчета"
    Given установлен идентификатор клиента "случайный 7-значный номер контракта"
    Given установлен идентификатор запроса "процентное значение 0.8, лимит 1000000"
    When Отправить "POST /mock-gateway/v1/calculation/profitability" на REST сервер "rest_mock" с хедерами "{"rqUid":"новый UUID для запроса расчета","rqTm":"текущая дата и время","spName":"urn:mock:autotest","systemId":"urn:mock:system"}" с body из файла "request_profitability.json"
    Then Проверить ответ с кодом 200
    Then заголовок ответа "rquid" содержит "newRequestId"
    When отправить GET запрос на сервер "rest_mock" endpoint "/mock-gateway/v1/reports/by-uid"
    Then Проверить ответ с кодом 200 и body
      """
      Проверка успешного ответа и наличия processIdentifier в теле
      """
    When отправить GET запрос на сервер "rest_mock" endpoint "/mock-gateway/v1/reports/by-id"
    When повторить последний запрос на сервер "rest_mock" 60 раз
    Then размер ответа больше 2048 байт
    Given установлен формат даты "первый день текущего месяца плюс 1 год"
    Then результат запроса соответствует данным:
    Then результат запроса соответствует данным:
    Then результат запроса соответствует данным:
