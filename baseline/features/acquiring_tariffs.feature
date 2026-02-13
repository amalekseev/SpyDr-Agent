@acquiring @tariffs
Feature: Acquiring Tariffs

  @check_all_tariffs
  Scenario: Проверка всех тарифов
    Given установлен идентификатор запроса "уникальный UUID для запроса"
    Given установлен формат даты "yyyy-MM-dd'T'HH:mm:ss"
    Given установлен идентификатор сессии "urn:mock:autotest, urn:mock:system"
    When Отправить "POST /mock-gateway/v1/tariffs/recommended" на REST сервер "rest_mock" с хедерами "rqUid: уникальный UUID, rqTm: текущая дата и время, spName: urn:mock:autotest, systemId: urn:mock:system" с body из файла "request_recommended.json"
    Then код ответа сервера "rest_mock" равен 200
    Then сравнить ответ с эталоном из файла "response_recommended.json"
    Given установлен идентификатор запроса "новый UUID для запроса расчета"
    Given установлен идентификатор клиента "случайное 7-значное число - уникальный номер контракта"
    Given установлен идентификатор сессии "urn:mock:autotest, urn:mock:system"
    When Отправить "POST /mock-gateway/v1/calculation/profitability" на REST сервер "rest_mock" с хедерами "rqUid: новый UUID, rqTm: текущее время, spName: urn:mock:autotest, systemId: urn:mock:system" с body из файла "request_profitability.json"
    Then Проверить ответ с кодом 200
    Then сохранить заголовок "rquid" из ответа в переменную "newRequestId"
    When отправить GET запрос на сервер "rest_mock" endpoint "/mock-gateway/v1/reports/by-uid?rqUid=newRequestId&periodBy=0"
    Then код ответа сервера "rest_mock" равен 200
    When отправить GET запрос на сервер "rest_mock" endpoint "/mock-gateway/v1/reports/by-id?processId=processIdentifier"
    When повторить последний запрос на сервер "rest_mock" 60 раз
    Then размер ответа больше 2048 байт
    Given установлен формат даты "первый день текущего месяца плюс 1 год"
    Then результат запроса соответствует данным:
      """
      Проверить, что рассчитанный тариф прибыльности за 1 год (payback_1year) положительный
      """
    Then результат запроса соответствует данным:
      """
      Проверить, что рассчитанный тариф прибыльности за 3 года (payback_3year) положительный
      """
    Then результат запроса соответствует данным:
      """
      Проверить, что рекомендованный тариф равен максимуму из payback_1year и 0.02
      """
