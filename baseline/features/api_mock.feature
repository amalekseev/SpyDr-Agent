Feature: Api Mock

  Scenario: Создание новой записи через API методом POST
    Given установлен базовый URL "https://api.example.com"
    Given установлен заголовок "Content-Type" со значением "application/json" для сервера "https://api.example.com"
    When отправить POST запрос на сервер "https://api.example.com" endpoint "/items" с телом:
      """
      {
        "name": "Новый элемент",
        "description": "Описание для теста"
      }
      """
    Then код ответа сервера "https://api.example.com" равен 200
    Then поле "status == success" имеет ошибку валидации
    Then сохранить значение поля "id" из ответа в переменную "item_id"

  Scenario: Получение данных записи по идентификатору через API методом GET
    Given установлен базовый URL "https://api.example.com"
    When отправить GET запрос на сервер "https://api.example.com" endpoint "/items/123"
    Then код ответа сервера "https://api.example.com" равен 200
    Then тело ответа содержит поле "name" со значением не равным "Mock Item"
