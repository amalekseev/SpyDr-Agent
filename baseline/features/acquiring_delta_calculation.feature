Feature: Acquiring Delta Calculation

  Scenario: Проверка расчета дельт при росте параметра
    Given установлен идентификатор запроса "requestId"
    And установлен идентификатор сессии "sessionId"
    And установлен формат даты "yyyy-MM-dd'T'HH:mm:ss"
    When вывести время ответа
    And присвоить переменной "requestTime" текущую дату в формате "yyyy-MM-dd'T'HH:mm:ss"
    And установить время "requestTime" в поле "body"
    And установлен идентификатор корреляции "correlationId"
    And включено логирование запросов
    When Отправить "/mock-gateway/v1/tariffs/recommended" на REST сервер "rest_mock" с хедерами "rqUid, rqTm, spName, systemId"
    And Отправить "/mock-gateway/v1/tariffs/recommended" на REST сервер "rest_mock" с хедерами "rqUid, rqTm, spName, systemId" с body из файла "request_recommended.json"
    Then отправить POST запрос на сервер "rest_mock" endpoint "/mock-gateway/v1/tariffs/recommended" с телом:
      """
      Отправка POST-запроса на сервер с телом.
      """
