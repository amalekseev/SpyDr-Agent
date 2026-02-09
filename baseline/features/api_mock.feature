Feature: Api Mock

  @api @items @create
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
    Then код ответа должен быть 200
    Then тело ответа содержит поле "status" со значением "success"
    Then сохранить значение поля "id" в переменную "item_id"

  @api @items @get
  Scenario: Получение данных записи по идентификатору через API методом GET
    Given установлен базовый URL "https://api.example.com"
    When отправить GET запрос на "/items/123"
    Then код ответа должен быть 200
    Then тело ответа содержит поле "name" со значением "Mock Item"
