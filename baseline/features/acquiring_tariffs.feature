Feature: Acquiring Tariffs

  Scenario: Проверка всех тарифов
    Given установлен идентификатор запроса "uuid_1"
    Given установлен формат даты "yyyy-MM-ddTHH:mm:ss"
    Given установлен идентификатор пользователя "urn:mock:autotest"
    Given установлен идентификатор клиента "urn:mock:system"
    When Отправить "POST /mock-gateway/v1/tariffs/recommended" на REST сервер "rest_mock" с хедерами "rqUid: uuid_1, rqTm: current_datetime, spName: urn:mock:autotest, systemId: urn:mock:system" с body из файла "request_recommended.json"
    Then код ответа сервера "rest_mock" равен 200
    Then сравнить ответ с эталоном из файла "response_recommended.json"
    Given установлен идентификатор запроса "uuid_2"
    Given установлен идентификатор клиента "contract_7digit"
    Given установлен идентификатор пользователя "percent_0.8_limit_1000000"
    When Отправить "POST /mock-gateway/v1/calculation/profitability" на REST сервер "rest_mock" с хедерами "rqUid: uuid_2, rqTm: current_datetime, spName: urn:mock:autotest, systemId: urn:mock:system" с body из файла "request_profitability.json"
    Then Проверить ответ с кодом 200
    Then заголовок ответа "rquid" существует
    When отправить GET запрос на сервер "rest_mock" endpoint "/mock-gateway/v1/reports/by-uid"
    Then Проверить ответ с кодом 200
    Then результат запроса в первой строке содержит "processIdentifier" в колонке "processIdentifier"
    When отправить GET запрос на сервер "rest_mock" endpoint "/mock-gateway/v1/reports/by-id"
    When отправить запрос с retry на сервер "rest_mock" endpoint "/mock-gateway/v1/reports/by-id" с 60 попытками
    Then размер ответа больше 2048 байт
    Given установлен формат даты "первый день текущего месяца плюс 1 год"
    Then результат запроса в первой строке содержит "0.025" в колонке "payback_1year"
    Then результат запроса в первой строке содержит "0.018" в колонке "payback_3year"
    Then результат запроса в первой строке содержит "max(payback_1year, 0.02)" в колонке "recommended_tariff"
