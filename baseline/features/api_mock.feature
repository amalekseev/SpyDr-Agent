Feature: Api Mock

  Scenario: Создание новой записи через API методом POST
    Given настроен REST клиент для сервера "api.example.com" с базовым URL "https://api.example.com"
    Given установлен Content-Type "application/json"
    When отправить POST запрос на сервер "api.example.com" endpoint "/items" с телом:
      """
      {
        "name": "Новый элемент",
        "description": "Описание для теста"
      }
      """
    Then Проверить ответ с кодом 200
    Then ответ содержит JSON поле "status"
    Then сохранить значение поля "id" из ответа в переменную "item_id"

  Scenario: Получение данных записи по идентификатору через API методом GET
    Given настроен REST клиент для сервера "api.example.com" с базовым URL "https://api.example.com"
    When отправить GET запрос на сервер "api.example.com" endpoint "/items/123"
    Then Проверить ответ с кодом 200
    Then сохранить значение поля "name" из ответа в переменную "expected_name"
