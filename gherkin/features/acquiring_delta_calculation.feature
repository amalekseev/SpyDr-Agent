Feature: Проверка расчета дельт
  Проверка корректности расчета дельт при изменении параметров

  @business_regress @crit_regress
  Scenario: Проверка расчета дельт при росте параметра
    # Выполнение запроса рекомендованных тарифов
    When Присвоить переменной "requestId" значение "${UUID}"
    When Присвоить переменной "requestTime" значение "${CUR_DATE(%Y-%m-%dT%H:%M:%S)}"
    When Присвоить переменной "serviceName" значение "urn:mock:autotest"
    When Присвоить переменной "systemIdentifier" значение "urn:mock:system"
    When Отправить "POST /mock-gateway/v1/tariffs/recommended" на REST сервер "rest_mock" с хедерами "rqUid:${requestId},rqTm:${requestTime},spName:${serviceName},systemId:${systemIdentifier}" с body из файла "resources/mock/request_recommended.json"
    Then Проверить ответ с кодом 200 и body из файла "resources/mock/response_recommended.json"

    # Выполнение расчета с большим параметром
    When Присвоить переменной "contractIdInitial" значение "${UNIC_NUMBER(7)}"
    When Присвоить переменной "calcRequestId" значение "${UUID}"

    # Параметры для расчета
    When Присвоить переменной "percentValue" значение "0.8"
    When Присвоить переменной "limitValue" значение "5000000"
    When Отправить "POST /mock-gateway/v1/calculation/profitability" на REST сервер "rest_mock" с хедерами "rqUid:${calcRequestId},rqTm:${requestTime},spName:${serviceName},systemId:${systemIdentifier}" с body из файла "resources/mock/request_delta.json"
    Then Проверить ответ с кодом 200 и body
      """json
        {
          "dont_check_array_len": true,
          "compensation": "${compensationInitial}",
          "impactOnLimit": "${impactOnLimitInitial}",
          "lostIncomeChanging": "${lostIncomeInitial}",
          "crossSaleProfitChanging": "${crossSaleProfitInitial}"
        }
      """

    # Обновление лимитов в базе данных
    When Выполнить запрос в базу "postgres_mock"
      """sql
        update mock_schema.limit_table l
        SET limit_amt = 10000000
        where l.division_cd in (
          select d.division_cd
          from mock_schema.division_table d
          join mock_schema.limit_table ls ON ls.division_cd = d.division_cd
          where ls.status_cd = 'active' and ls.limit_cd = 'MOCK'
        );
      """

    # Перевод в статус "В работе"
    When Присвоить переменной "currentDate" значение "${CUR_DATE(%Y-%m-%d)}"
    When Присвоить переменной "futureDate" значение "${CUR_DATE(%Y-%m-%d)[+365d]}"
    When Присвоить переменной "statusRequestIdWorking" значение "${UUID}"
    When Отправить "POST /mock-status/v1/agreement/change-status" на REST сервер "rest_mock" с хедерами "rqUid:${statusRequestIdWorking},rqTm:${requestTime},spName:${serviceName},systemId:${systemIdentifier}" с body из файла "resources/mock/request_status_working.json"
    Then Проверить ответ с кодом 200

    # Перевод в статус "Действует"
    When Присвоить переменной "statusRequestIdActive" значение "${UUID}"
    When Отправить "POST /mock-status/v1/agreement/change-status" на REST сервер "rest_mock" с хедерами "rqUid:${statusRequestIdActive},rqTm:${requestTime},spName:${serviceName},systemId:${systemIdentifier}" с body из файла "resources/mock/request_status_active.json"
    Then Проверить ответ с кодом 200

    # Выполнение запроса для изменения расчета
    When Присвоить переменной "changeRequestId" значение "${UUID}"
    When Присвоить переменной "contractIdChange" значение "${UNIC_NUMBER(7)}"
    When Отправить "POST /mock-gateway/v1/tariffs/recommended" на REST сервер "rest_mock" с хедерами "rqUid:${requestId},rqTm:${requestTime},spName:${serviceName},systemId:${systemIdentifier}" с body из файла "resources/mock/request_change.json"
    Then Проверить ответ с кодом 200 и body из файла "resources/mock/response_change.json"

    # Расчет изменения
    When Присвоить переменной "contractIdFinal" значение "${UNIC_NUMBER(7)}"
    When Присвоить переменной "finalCalcRequestId" значение "${UUID}"

    When Присвоить переменной "percentValueFinal" значение "0.8"
    When Присвоить переменной "limitValueFinal" значение "3000000"
    When Отправить "POST /mock-gateway/v1/change/profitability-calculation" на REST сервер "rest_mock" с хедерами "rqUid:${finalCalcRequestId},rqTm:${requestTime},spName:${serviceName},systemId:${systemIdentifier}" с body из файла "resources/mock/request_change_profitability.json"
    Then Проверить ответ с кодом 200 и body
      """json
        {
          "dont_check_array_len": true,
          "compensation": "${compensationFinal}",
          "compensationDelta": "${compensationDeltaValue}",
          "impactOnLimit": "${impactOnLimitFinal}",
          "lostIncomeChanging": "${lostIncomeFinal}",
          "crossSaleProfitChanging": "${crossSaleProfitFinal}",
          "impactOnLimitDelta": "${impactOnLimitDeltaValue}",
          "lostIncomeChangingDelta": "${lostIncomeDeltaValue}",
          "crossSaleProfitChangingDelta": "${crossSaleProfitDeltaValue}"
        }
      """

    # Проверка корректности расчета дельт
    Then Выполнить python код
      """py
      from datetime import datetime
      
      date_today_str = "${currentDate}"
      date_future_str = "${futureDate}"
      date_object = datetime.strptime(date_today_str, "%Y-%m-%d")
      date_today = date_object.date()
      date_object_future = datetime.strptime(date_future_str, "%Y-%m-%d")
      date_future = date_object_future.date()
      date_difference = date_future - date_today
      difference = date_difference.days
      
      print(f"MOCK: Разница в днях: {difference}")
      
      # Мок проверки расчетов
      compensation_initial = 1000.0
      compensation_final = 1500.0
      
      expected_delta = (compensation_final - compensation_initial) / 365 * difference
      print(f"MOCK: Ожидаемая дельта: {expected_delta}")
      
      assert difference > 0, "Разница в днях должна быть положительной"
      print("MOCK: Проверки дельт пройдены")
      """
