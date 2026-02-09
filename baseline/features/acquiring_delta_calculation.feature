Feature: Acquiring Delta Calculation

  @api @calculation @delta
  Scenario: Проверка расчета дельт при росте параметра
    Given настроен REST клиент для сервера "rest_mock"
    Given установлено подключение к базе данных "postgres_mock"
    When присвоить переменной "requestId" случайную строку длиной 32
    When присвоить переменной "requestTime" текущую дату в формате "yyyy-MM-dd'T'HH:mm:ss"
    When присвоить переменной "serviceName" значение "urn:mock:autotest"
    When присвоить переменной "systemIdentifier" значение "urn:mock:system"
    When присвоить переменной "spName" значение "urn:mock:autotest"
    When присвоить переменной "systemId" значение "urn:mock:system"
    When отправить POST запрос на сервер "rest_mock" endpoint "/mock-gateway/v1/tariffs/recommended" с телом:
      """
      file:request_recommended.json
      """
    Then код ответа сервера "rest_mock" равен 200
    Then сравнить ответ с эталоном из файла "response_recommended.json"
    When присвоить переменной "contractIdInitial" случайное число от 1000000 до 9999999
    When присвоить переменной "calcRequestId" случайную строку длиной 36
    When присвоить переменной "percentValue" значение "0.8"
    When присвоить переменной "limitValue" значение "5000000"
    When отправить POST запрос на сервер "rest_mock" endpoint "/mock-gateway/v1/calculation/profitability" с телом:
      """
      file:request_delta.json
      """
    Then код ответа сервера "rest_mock" равен 200
    Then тело ответа содержит поле "compensation"
    Then сохранить значение поля "compensation" из ответа в переменную "compensationInitial"
    Then тело ответа содержит поле "impactOnLimit"
    Then сохранить значение поля "impactOnLimit" из ответа в переменную "impactOnLimitInitial"
    Then тело ответа содержит поле "lostIncomeChanging"
    Then сохранить значение поля "lostIncomeChanging" из ответа в переменную "lostIncomeInitial"
    Then тело ответа содержит поле "crossSaleProfitChanging"
    Then сохранить значение поля "crossSaleProfitChanging" из ответа в переменную "crossSaleProfitInitial"
    When выполнить SQL запрос в базу "postgres_mock":
      """
      update mock_schema.limit_table set limit_amt = 10000000 where division_cd in (
        select t1.division_cd from mock_schema.division_table t1
        inner join mock_schema.limit_table t2 on t1.division_cd = t2.division_cd
        where t1.status_cd = 'active' and t2.limit_cd = 'MOCK'
      );
      """
    When присвоить переменной "currentDate" текущую дату в формате "yyyy-MM-dd"
    When присвоить переменной "futureDate" дату через 365 дней
    When присвоить переменной "statusRequestIdWorking" случайную строку длиной 36
    When отправить POST запрос на сервер "rest_mock" endpoint "/mock-status/v1/agreement/change-status" с телом:
      """
      file:request_status_working.json
      """
    Then код ответа сервера "rest_mock" равен 200
    When присвоить переменной "statusRequestIdActive" случайную строку длиной 36
    When отправить POST запрос на сервер "rest_mock" endpoint "/mock-status/v1/agreement/change-status" с телом:
      """
      file:request_status_active.json
      """
    Then код ответа сервера "rest_mock" равен 200
    When присвоить переменной "changeRequestId" случайную строку длиной 36
    When присвоить переменной "contractIdChange" случайное число от 1000000 до 9999999
    When отправить POST запрос на сервер "rest_mock" endpoint "/mock-gateway/v1/tariffs/recommended" с телом:
      """
      file:request_change.json
      """
    Then код ответа сервера "rest_mock" равен 200
    Then сравнить ответ с эталоном из файла "response_change.json"
    When присвоить переменной "contractIdFinal" случайное число от 1000000 до 9999999
    When присвоить переменной "finalCalcRequestId" случайную строку длиной 36
    When присвоить переменной "percentValueFinal" значение "0.8"
    When присвоить переменной "limitValueFinal" значение "3000000"
    When отправить POST запрос на сервер "rest_mock" endpoint "/mock-gateway/v1/change/profitability-calculation" с телом:
      """
      file:request_change_profitability.json
      """
    Then код ответа сервера "rest_mock" равен 200
    Then тело ответа содержит поле "compensation"
    Then сохранить значение поля "compensation" из ответа в переменную "compensationFinal"
    Then тело ответа содержит поле "compensationDelta"
    Then сохранить значение поля "compensationDelta" из ответа в переменную "compensationDeltaValue"
    Then тело ответа содержит поле "impactOnLimit"
    Then сохранить значение поля "impactOnLimit" из ответа в переменную "impactOnLimitFinal"
    Then тело ответа содержит поле "impactOnLimitDelta"
    Then сохранить значение поля "impactOnLimitDelta" из ответа в переменную "impactOnLimitDeltaValue"
    Then тело ответа содержит поле "lostIncomeChanging"
    Then сохранить значение поля "lostIncomeChanging" из ответа в переменную "lostIncomeFinal"
    Then тело ответа содержит поле "lostIncomeChangingDelta"
    Then сохранить значение поля "lostIncomeChangingDelta" из ответа в переменную "lostIncomeDeltaValue"
    Then тело ответа содержит поле "crossSaleProfitChanging"
    Then сохранить значение поля "crossSaleProfitChanging" из ответа в переменную "crossSaleProfitFinal"
    Then тело ответа содержит поле "crossSaleProfitChangingDelta"
    Then сохранить значение поля "crossSaleProfitChangingDelta" из ответа в переменную "crossSaleProfitDeltaValue"
    When Комментарий "Рассчитать разницу в днях между currentDate и futureDate и проверить, что положительная"
    Then переменная "futureDate" больше "currentDate"
    When Комментарий "Проверить, что compensationDeltaValue = (compensationFinal - compensationInitial) / 365 * количество дней"
    Then тест завершен успешно
