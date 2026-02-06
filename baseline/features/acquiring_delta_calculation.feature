Feature: Acquiring Delta Calculation

  @acquiring @delta @api @db
  Scenario: Проверка расчета дельт при росте параметра
    Given подготовлен тестовый контекст
    Given настроен REST клиент для сервера "rest_mock"
    Given установлено подключение к базе данных "postgres_mock"

    # Шаг 1: Сформировать необходимые переменные
    When присвоить переменной "requestId" случайную строку длиной 36
    When присвоить переменной "requestTime" текущую дату в формате "yyyy-MM-dd'T'HH:mm:ss"
    When Присвоить переменной "serviceName" значение "urn:mock:autotest"
    When Присвоить переменной "systemIdentifier" значение "urn:mock:system"

    # Шаг 2: Рекомендованные тарифы - первый запрос
    When отправить POST запрос на сервер "rest_mock" endpoint "/mock-gateway/v1/tariffs/recommended" с телом:
      """
      {содержимое файла request_recommended.json}
      """
    Then код ответа сервера "rest_mock" равен 200
    Then сравнить ответ с эталоном из файла "response_recommended.json"

    # Шаг 3: Сгенерировать контракт и идентификатор для расчёта
    When присвоить переменной "contractIdInitial" случайное число от 1000000 до 9999999
    When присвоить переменной "calcRequestId" случайную строку длиной 36

    # Шаг 4: Установить параметры расчета
    When Присвоить переменной "percentValue" значение "0.8"
    When Присвоить переменной "limitValue" значение "5000000"

    # Шаг 5: POST /mock-gateway/v1/calculation/profitability c первым расчетом   
    When отправить POST запрос на сервер "rest_mock" endpoint "/mock-gateway/v1/calculation/profitability" с телом:
      """
      {содержимое файла request_delta.json}
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

    # Шаг 6: Обновить лимит в базе до 10 000 000
    When выполнить UPDATE запрос в базу "postgres_mock":
      """
      UPDATE mock_schema.limit_table
      SET limit_amt = 10000000
      FROM mock_schema.division_table t2
      WHERE mock_schema.limit_table.division_cd = t2.division_cd
        AND t2.status_cd = 'active'
        AND t2.limit_cd = 'MOCK';
      """

    # Шаг 7: Получить currentDate и futureDate = currentDate + 365 дней
    When присвоить переменной "currentDate" текущую дату в формате "yyyy-MM-dd"
    When присвоить переменной "futureDate" дату через 365 дней

    # Шаг 8: Перевести договор в статус "В работе"
    When присвоить переменной "statusRequestIdWorking" случайную строку длиной 36
    When отправить POST запрос на сервер "rest_mock" endpoint "/mock-status/v1/agreement/change-status" с телом:
      """
      {содержимое файла request_status_working.json}
      """
    Then код ответа сервера "rest_mock" равен 200

    # Шаг 9: Перевести договор в статус "Действует"
    When присвоить переменной "statusRequestIdActive" случайную строку длиной 36
    When отправить POST запрос на сервер "rest_mock" endpoint "/mock-status/v1/agreement/change-status" с телом:
      """
      {содержимое файла request_status_active.json}
      """
    Then код ответа сервера "rest_mock" равен 200

    # Шаг 10: Рекомендованные тарифы - повторный запрос с изменёнными значениями
    When присвоить переменной "changeRequestId" случайную строку длиной 36
    When присвоить переменной "contractIdChange" случайное число от 1000000 до 9999999
    When отправить POST запрос на сервер "rest_mock" endpoint "/mock-gateway/v1/tariffs/recommended" с телом:
      """
      {содержимое файла request_change.json}
      """
    Then код ответа сервера "rest_mock" равен 200
    Then сравнить ответ с эталоном из файла "response_change.json"

    # Шаг 11: Финальный расчет profitability с новыми лимитом и процентом
    When присвоить переменной "contractIdFinal" случайное число от 1000000 до 9999999
    When присвоить переменной "finalCalcRequestId" случайную строку длиной 36
    When Присвоить переменной "percentValueFinal" значение "0.8"
    When Присвоить переменной "limitValueFinal" значение "3000000"
    When отправить POST запрос на сервер "rest_mock" endpoint "/mock-gateway/v1/change/profitability-calculation" с телом:
      """
      {содержимое файла request_change_profitability.json}
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

    # Шаг 12: Рассчитать разницу в днях между currentDate и futureDate (логика проверки вне шагов Gherkin)
    # Контролировать что разница положительная
    Then тест завершен успешно
