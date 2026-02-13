Feature: Kncu Integration

  Scenario: Проверка корректности обработки запроса типа A внешним сервисом
    Given установлен идентификатор корреляции "UUID"
    When отправить POST запрос на сервер "external-integration" endpoint "/execute" с телом:
      """
      {
        "file_path": "type_a_req.json"
      }
      """
    Then код ответа сервера "external-integration" равен 200
    Then сравнить ответ с эталоном из файла "type_a_res.json"

  Scenario: Проверка корректности обработки запроса типа B внешним сервисом
    Given установлен идентификатор корреляции "UUID"
    When отправить POST запрос на сервер "external-integration" endpoint "/execute" с телом:
      """
      {
        "file_path": "type_b_req.json"
      }
      """
    Then код ответа сервера "external-integration" равен 200
    Then сравнить ответ с эталоном из файла "type_b_res.json"

  Scenario: Проверка корректности обработки запроса типа C внешним сервисом
    Given установлен идентификатор корреляции "UUID"
    When отправить POST запрос на сервер "external-integration" endpoint "/execute" с телом:
      """
      {
        "file_path": "type_c_req.json"
      }
      """
    Then код ответа сервера "external-integration" равен 200
    Then сравнить ответ с эталоном из файла "type_c_res.json"
