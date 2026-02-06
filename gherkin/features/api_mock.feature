Feature: API Testing (Mock)

  Scenario: Successful record creation via POST
    Given установлен базовый URL "https://api.example.com"
    And заголовок "Content-Type" имеет значение "application/json"
    When отправить POST запрос на "/items" с телом:
    """
    {
      "name": "Новый элемент",
      "description": "Описание для теста"
    }
    """
    Then код ответа должен быть 200
    And тело ответа содержит поле "status" со значением "success"
    And сохранить значение поля "id" в переменную "item_id"

  Scenario: Get data via GET
    Given установлен базовый URL "https://api.example.com"
    When отправить GET запрос на "/items/123"
    Then код ответа должен быть 200
    And тело ответа содержит поле "name" со значением "Mock Item"
