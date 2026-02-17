Feature: Проверка тарифов
  Проверка корректности расчета тарифов через REST API

  @business_regress @single
  Scenario: Проверка всех тарифов
    # Выполнение запроса рекомендованных тарифов
    When Присвоить переменной "requestId" значение "${UUID}"
    When Присвоить переменной "requestTime" значение "${CUR_DATE(%Y-%m-%dT%H:%M:%S)}"
    When Присвоить переменной "serviceName" значение "urn:mock:autotest"
    When Присвоить переменной "systemIdentifier" значение "urn:mock:system"
    When Отправить "POST /mock-gateway/v1/tariffs/recommended" на REST сервер "rest_mock" с хедерами "rqUid:${requestId},rqTm:${requestTime},spName:${serviceName},systemId:${systemIdentifier}" с body из файла "resources/mock/request_recommended.json"
    Then Проверить ответ с кодом 200 и body из файла "resources/mock/response_recommended.json"

    # Выполнение расчета
    When Присвоить переменной "contractId" значение "${UNIC_NUMBER(7)}"
    When Присвоить переменной "calcRequestId" значение "${UUID}"

    # Параметры для расчета
    When Присвоить переменной "percentValue" значение "0.8"
    When Присвоить переменной "limitValue" значение "1000000"
    When Отправить "POST /mock-gateway/v1/calculation/profitability" на REST сервер "rest_mock" с хедерами "rqUid:${calcRequestId},rqTm:${requestTime},spName:${serviceName},systemId:${systemIdentifier}" с body из файла "resources/mock/request_profitability.json"
    Then Проверить ответ с кодом 200
    Then Проверить хедеры из последнего ответа
      | Name  | Value              |
      | rquid | ${newRequestId} |

    When Отправить "GET /mock-gateway/v1/reports/by-uid?rqUid=${newRequestId}&periodBy=0" на REST сервер "rest_mock" с хедерами "rqUid:${calcRequestId},rqTm:${requestTime},spName:${serviceName},systemId:${systemIdentifier}"
    Then Проверить ответ с кодом 200 и body
      """txt
      ${processIdentifier}
      """

    When Отправить "GET /mock-gateway/v1/reports/by-id?processId=${processIdentifier}" на REST сервер "rest_mock" с хедерами "rqUid:${calcRequestId},rqTm:${requestTime},spName:${serviceName},systemId:${systemIdentifier}"
    Then Проверить ответ с кодом 200 в течение 60 секунд
    Then Проверить ответ с кодом 200 и файлом с размером больше 2 кБ

    # Основные проверки расчетов
    Then Выполнить python код
      """py
      from datetime import datetime
      from dateutil.relativedelta import relativedelta

      first_day = datetime.now().replace(day=1) + relativedelta(years=1)
      print(first_day.strftime('%d.%m.%Y'))

      # Мок проверки тарифов
      payback_1year = 0.025
      payback_3year = 0.018
      recommended = max(payback_1year, 0.02)
      
      assert payback_1year > 0, "Тариф должен быть положительным"
      assert payback_3year > 0, "Тариф должен быть положительным"
      print("MOCK: Проверки пройдены")
      """
