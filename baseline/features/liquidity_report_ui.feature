@UI @Negative
Feature: Liquidity Report Ui

  @UI @Negative
  Scenario: [UI][Negative] Проверка экспорта отчета при пустых сущностях
    Given базовая авторизация логин "MOCK_LOGIN" пароль "MOCK_PASSWORD"
    When Сформировать отчет
    Then элемент "div" имеет точный текст "Сущности не должны быть пустыми"
