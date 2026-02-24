Feature: Api Mock

  Scenario: Создание новой записи через API методом POST
    Given установлен базовый URL "https://api.example.com"
    And установлен Content-Type "application/json"
    And отправить запрос с кастомным Content-Type "application/json" на сервер "https://api.example.com" endpoint "/items":
      """
      Отправка запроса с кастомным Content-Type.
      """
    And отправить POST запрос на "/items" с телом:
      """
      Отправка POST запроса на /items с телом.
      """
    When отправить POST запрос на "/items" с телом:
      """
      Отправка POST запроса на /items с телом.
      """
    And ответ является валидным JSON
    And отправить POST запрос на "/items" с телом:
      """
      Отправка POST запроса на /items с телом.
      """
    And ответ является валидным JSON
    And отправить POST запрос на "/items" с телом:
      """
      Отправка POST запроса на /items с телом.
      """
    And ответ является валидным JSON
    And отправить POST запрос на "/items" с телом:
      """
      Отправка POST запроса на /items с телом.
      """

  Scenario: Получение данных записи по идентификатору через API методом GET
    Given отправить GET запрос на сервер "https://api.example.com" endpoint "/items/123"
    When отправить GET запрос на сервер "https://api.example.com" endpoint "/items/123"
    And код ответа сервера "https://api.example.com" равен 200
    And отправить GET запрос на "/items/123"
    Then отправить GET запрос на "/items/123"
    And тело ответа содержит поле "name" типа "str"
    And тело ответа содержит поле "name" со значением больше Mock Item
