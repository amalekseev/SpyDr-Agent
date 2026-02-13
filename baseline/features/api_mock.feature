Feature: Api Mock

  Scenario: Создание новой записи через API методом POST
    Given настроен REST клиент для сервера "API" с базовым URL "https://api.example.com"
    Given установлен заголовок "Content-Type" со значением "application/json" для сервера "API"
    When отправить POST запрос на сервер "API" endpoint "/items" с телом:
      """
      {
        "name": "Новый элемент",
        "description": "Описание для теста"
      }
      """
    Then код ответа сервера "API" равен 200
    Then тело ответа содержит поле "status" со значением "success"
    Then сохранить значение поля "id" из ответа в переменную "item_id"

  Scenario: Получение данных записи по идентификатору через API методом GET
    Given настроен REST клиент для сервера "API" с базовым URL "https://api.example.com"
    When отправить GET запрос на сервер "API" endpoint "/items/123"
    Then код ответа сервера "API" равен 200
    Then тело ответа содержит поле "name" со значением "Mock Item"
