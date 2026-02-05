@api @mock
Feature: Api Mock

  @post @create
  Scenario: Успешное создание записи через POST
    Given установлен базовый URL "https://api.example.com"
    And заголовок "Content-Type" имеет значение "application/json"
    When отправить POST запрос на "/items" с телом:
      """
      {
        "name": "Новый элемент",
        "description": "Описание для теста"
      }
      """
    Then код ответа должен быть 201
    And тело ответа содержит поле "status" со значением "success"
    And сохранить значение поля "id" в переменную "item_id"

  @get @read
  Scenario: Получение данных через GET
    Given установлен базовый URL "https://api.example.com"
    When отправить GET запрос на "/items/123"
    Then код ответа должен быть 200
    And тело ответа содержит поле "name" со значением "Mock Item"
