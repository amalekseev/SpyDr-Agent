@acquiring @delta @calculation
Feature: Acquiring Delta Calculation

  @delta_calculation @growth
  Scenario: Проверка расчета дельт при росте параметра
    Given установлен идентификатор запроса "requestId"
    When Отправить "/mock-gateway/v1/tariffs/recommended" на REST сервер "rest_mock" с хедерами "rqUid, rqTm, spName, systemId" с body из файла "request_recommended.json"
    Then код ответа сервера "rest_mock" равен 200
    Then ответ является валидным JSON
    Given установлен идентификатор запроса "calcRequestId"
    Given установлен максимальный размер ответа 5000000 МБ
    When Отправить "/mock-gateway/v1/calculation/profitability" на REST сервер "rest_mock" с хедерами "rqUid=calcRequestId, serviceName=urn:mock:autotest, systemIdentifier=urn:mock:system" с body из файла "request_delta.json"
    Then код ответа сервера "rest_mock" равен 200
    Then ответ является валидным JSON
    When выполнить UPDATE запрос в базу "postgres_mock":
      """
      Выполнить UPDATE запрос в базу "postgres_mock":
      update mock_schema.limit_table set limit_amt = 10000000 where division_cd in (select division_cd from mock_schema.division_table where status_cd = 'active') and limit_cd = 'MOCK';
      """
    Given установлен формат даты "yyyy-MM-dd'T'HH:mm:ss"
    Given установлен идентификатор запроса "statusRequestIdWorking"
    When Отправить "/mock-status/v1/agreement/change-status" на REST сервер "rest_mock" с хедерами "rqUid=statusRequestIdWorking, serviceName=urn:mock:autotest, systemIdentifier=urn:mock:system" с body из файла "request_status_working.json"
    Then код ответа сервера "rest_mock" равен 200
    Given установлен идентификатор запроса "statusRequestIdActive"
    When Отправить "/mock-status/v1/agreement/change-status" на REST сервер "rest_mock" с хедерами "rqUid=statusRequestIdActive, serviceName=urn:mock:autotest, systemIdentifier=urn:mock:system" с body из файла "request_status_active.json"
    Then код ответа сервера "rest_mock" равен 200
    Given установлен идентификатор запроса "changeRequestId"
    When Отправить "/mock-gateway/v1/tariffs/recommended" на REST сервер "rest_mock" с хедерами "rqUid=requestId, serviceName=urn:mock:autotest, systemIdentifier=urn:mock:system" с body из файла "request_change.json"
    Then код ответа сервера "rest_mock" равен 200
    Then ответ является валидным JSON
    Given установлен идентификатор запроса "finalCalcRequestId"
    Given установлен максимальный размер ответа 3000000 МБ
    When Отправить "/mock-gateway/v1/change/profitability-calculation" на REST сервер "rest_mock" с хедерами "rqUid=finalCalcRequestId, serviceName=urn:mock:autotest, systemIdentifier=urn:mock:system" с body из файла "request_change_profitability.json"
    Then код ответа сервера "rest_mock" равен 200
    Then ответ является валидным JSON
    Then переменная "daysDifference" больше 0
    Then переменная "daysDifference" больше 1
    Then переменная "compensationDelta" больше 0
