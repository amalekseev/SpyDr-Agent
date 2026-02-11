Feature: Acquiring Delta Calculation

  Scenario: Проверка расчета дельт при росте параметра
    Given установлен идентификатор запроса "requestId"
    When Отправить "/mock-gateway/v1/tariffs/recommended" на REST сервер "rest_mock" с хедерами "rqUid, rqTm, spName, systemId" с body из файла "request_recommended.json"
    Then код ответа сервера "rest_mock" равен 200
    Then ответ является валидным JSON
    Given установлен идентификатор запроса "calcRequestId"
    Given установлен идентификатор запроса "contractIdInitial"
    Given установлен максимальный размер ответа 5000000 МБ
    When Отправить "/mock-gateway/v1/calculation/profitability" на REST сервер "rest_mock" с хедерами "rqUid=calcRequestId, spName, systemId" с body из файла "request_delta.json"
    Then код ответа сервера "rest_mock" равен 200
    When выполнить UPDATE запрос в базу "postgres_mock":
      """
      UPDATE mock_schema.limit_table SET limit_amt = 10000000 WHERE division_cd IN (SELECT division_cd FROM mock_schema.division_table WHERE status_cd = 'active' AND limit_cd = 'MOCK');
      """
    Given установлен формат даты "yyyy-MM-dd"
    When Отправить "/mock-status/v1/agreement/change-status" на REST сервер "rest_mock" с хедерами "rqUid=statusRequestIdWorking, spName, systemId" с body из файла "request_status_working.json"
    Then код ответа сервера "rest_mock" равен 200
    When Отправить "/mock-status/v1/agreement/change-status" на REST сервер "rest_mock" с хедерами "rqUid=statusRequestIdActive, spName, systemId" с body из файла "request_status_active.json"
    Then код ответа сервера "rest_mock" равен 200
    When Отправить "/mock-gateway/v1/tariffs/recommended" на REST сервер "rest_mock" с хедерами "rqUid=requestId, spName, systemId" с body из файла "request_change.json"
    Then Проверить ответ с кодом 200 и body из файла "response_change.json"
    Given установлен идентификатор запроса "finalCalcRequestId"
    Given установлен максимальный размер ответа 3000000 МБ
    When Отправить "/mock-gateway/v1/change/profitability-calculation" на REST сервер "rest_mock" с хедерами "rqUid=finalCalcRequestId, spName, systemId" с body из файла "request_change_profitability.json"
    Then код ответа сервера "rest_mock" равен 200
