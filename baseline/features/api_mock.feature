Feature: Api Mock

  Scenario: Создание новой записи через API методом POST
    Given установлен базовый URL "https://api.example.com"
    Given установлен Content-Type "application/json"
    When отправить POST запрос на "/items" с телом:
      """
      {
        "name": "Новый элемент",
        "description": "Описание для теста"
      }
      """
    Then код ответа сервера "https://api.example.com" равен 200
    Then ответ содержит JSON поле "status"
    Then сохранить значение вложенного поля "id" из ответа в переменную "item_id"

  Scenario: Получение данных записи по идентификатору через API методом GET
    Given установлен базовый URL "https://api.example.com"
    When отправить GET запрос на "/items/123"
    Then код ответа сервера "https://api.example.com" равен 200
    Then тело ответа содержит поле "name" со значением не равным "Mock Item"
