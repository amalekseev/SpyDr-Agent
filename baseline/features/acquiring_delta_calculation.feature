@acquiring @delta @calculation
Feature: Acquiring Delta Calculation

  @delta_calculation @growth
  Scenario: Проверка расчета дельт при росте параметра
    Given включено логирование запросов
    Given установлен идентификатор запроса "requestId"
    Given установлен идентификатор сессии "requestTime"
    Given установлен идентификатор клиента "urn:mock:autotest"
    Given установлен идентификатор корреляции "urn:mock:system"
    When отправить POST запрос на сервер "rest_mock" endpoint "/mock-gateway/v1/tariffs/recommended" с телом:
      """
      {
        "headers": "rqUid, rqTm, spName, systemId",
        "file_path": "request_recommended.json"
      }
      """
    Then код ответа сервера "rest_mock" равен 200
    Then ответ является валидным JSON
    Given установлен идентификатор запроса "contractIdInitial"
    Given установлен идентификатор запроса "calcRequestId"
    Given установлен идентификатор клиента "0.8"
    Given установлен идентификатор клиента "5000000"
    When отправить POST запрос на сервер "rest_mock" endpoint "/mock-gateway/v1/calculation/profitability" с телом:
      """
      {
        "headers": "rqUid=calcRequestId, spName, systemId",
        "file_path": "request_delta.json"
      }
      """
    Then Проверить ответ с кодом 200 и body
      """
      Проверить что ответ содержит поля compensation, impactOnLimit, lostIncomeChanging, crossSaleProfitChanging и сохранить их значения
      """
    When выполнить UPDATE запрос в базу "postgres_mock":
      """
      UPDATE mock_schema.limit_table SET limit_amt = 10000000 WHERE division_cd IN (SELECT division_cd FROM mock_schema.division_table WHERE status_cd = 'active') AND limit_cd = 'MOCK';
      """
    Given установлен формат даты "currentDate"
    Given установлен формат даты "futureDate"
    When отправить POST запрос на сервер "rest_mock" endpoint "/mock-status/v1/agreement/change-status" с телом:
      """
      {
        "headers": "rqUid=statusRequestIdWorking, spName, systemId",
        "file_path": "request_status_working.json"
      }
      """
    Then код ответа сервера "rest_mock" равен 200
    When отправить POST запрос на сервер "rest_mock" endpoint "/mock-status/v1/agreement/change-status" с телом:
      """
      {
        "headers": "rqUid=statusRequestIdActive, spName, systemId",
        "file_path": "request_status_active.json"
      }
      """
    Then код ответа сервера "rest_mock" равен 200
    Given установлен идентификатор запроса "changeRequestId"
    Given установлен идентификатор запроса "contractIdChange"
    When отправить POST запрос на сервер "rest_mock" endpoint "/mock-gateway/v1/tariffs/recommended" с телом:
      """
      {
        "headers": "rqUid=requestId, spName, systemId",
        "file_path": "request_change.json"
      }
      """
    Then код ответа сервера "rest_mock" равен 200
    Then ответ является валидным JSON
    Given установлен идентификатор запроса "contractIdFinal"
    Given установлен идентификатор запроса "finalCalcRequestId"
    Given установлен идентификатор клиента "0.8"
    Given установлен идентификатор клиента "3000000"
    When отправить POST запрос на сервер "rest_mock" endpoint "/mock-gateway/v1/change/profitability-calculation" с телом:
      """
      {
        "headers": "rqUid=finalCalcRequestId, spName, systemId",
        "file_path": "request_change_profitability.json"
      }
      """
    Then Проверить ответ с кодом 200 и body
      """
      Проверить что ответ содержит поля compensation, compensationDelta, impactOnLimit, impactOnLimitDelta, lostIncomeChanging, lostIncomeChangingDelta, crossSaleProfitChanging, crossSaleProfitChangingDelta и сохранить их значения
      """
    When присвоить переменной "daysDifference" дату 365 дней назад
    Then результат запроса не пустой
    Then переменная "daysDifference" больше 0
    Then Проверить ответ с кодом 200 и body
      """
      Проверить что дельта компенсации соответствует формуле: (compensationFinal - compensationInitial) / 365 * количество дней
      """
