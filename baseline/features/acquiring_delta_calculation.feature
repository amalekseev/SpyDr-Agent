@acquiring @delta @calculation
Feature: Acquiring Delta Calculation

  @delta_calculation @growth
  Scenario: Проверка расчета дельт при росте параметра
    Given включено логирование запросов для сервера "rest_mock"
    When Отправить "/mock-gateway/v1/tariffs/recommended" на REST сервер "rest_mock" с хедерами "rqUid, rqTm, spName, systemId" с body из файла "request_recommended.json"
    Then Проверить ответ с кодом 200 и body из файла "response_recommended.json"
    Given установлен идентификатор запроса "calcRequestId"
    Given установлен идентификатор запроса "contractIdInitial"
    Given установлен идентификатор запроса "percentValue"
    Given установлен идентификатор запроса "limitValue"
    When Отправить "/mock-gateway/v1/calculation/profitability" на REST сервер "rest_mock" с хедерами "rqUid=calcRequestId, serviceName=urn:mock:autotest, systemIdentifier=urn:mock:system" с body из файла "request_delta.json"
    Then Проверить ответ с кодом 200 и body
      """
      Проверка успешного получения ответа с кодом 200 и JSON телом.
      """
    When выполнить UPDATE запрос в базу "postgres_mock":
      """
      Выполнить UPDATE запрос в базу.
      """
    Given установлен формат даты "yyyy-MM-dd'T'HH:mm:ss"
    When Отправить "/mock-status/v1/agreement/change-status" на REST сервер "rest_mock" с хедерами "rqUid=statusRequestIdWorking, serviceName=urn:mock:autotest, systemIdentifier=urn:mock:system" с body из файла "request_status_working.json"
    Then Проверить ответ с кодом 200 и body
      """
      Проверка успешного получения ответа с кодом 200 и JSON телом.
      """
    When Отправить "/mock-status/v1/agreement/change-status" на REST сервер "rest_mock" с хедерами "rqUid=statusRequestIdActive, serviceName=urn:mock:autotest, systemIdentifier=urn:mock:system" с body из файла "request_status_active.json"
    Then Проверить ответ с кодом 200 и body
      """
      Проверка успешного получения ответа с кодом 200 и JSON телом.
      """
    When Отправить "/mock-gateway/v1/tariffs/recommended" на REST сервер "rest_mock" с хедерами "rqUid=requestId, serviceName=urn:mock:autotest, systemIdentifier=urn:mock:system" с body из файла "request_change.json"
    Then Проверить ответ с кодом 200 и body из файла "response_change.json"
    Given установлен идентификатор запроса "contractIdFinal"
    Given установлен идентификатор запроса "finalCalcRequestId"
    Given установлен идентификатор запроса "percentValueFinal"
    Given установлен идентификатор запроса "limitValueFinal"
    When Отправить "/mock-gateway/v1/change/profitability-calculation" на REST сервер "rest_mock" с хедерами "rqUid=finalCalcRequestId, serviceName=urn:mock:autotest, systemIdentifier=urn:mock:system" с body из файла "request_change_profitability.json"
    Then Проверить ответ с кодом 200 и body
      """
      Проверка успешного получения ответа с кодом 200 и JSON телом.
      """
    When присвоить переменной "daysDifference" текущую дату в формате "yyyy-MM-dd'T'HH:mm:ss"
    Then результат запроса не пустой
    Then тело полученного сообщения равно:
      """
      Проверка точного соответствия тела сообщения.
      """
