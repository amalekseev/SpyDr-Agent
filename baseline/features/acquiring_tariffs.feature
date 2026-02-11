@acquiring @tariffs
Feature: Acquiring Tariffs

  @check_all_tariffs
  Scenario: Проверка всех тарифов
    Given установлен идентификатор запроса "уникальный UUID"
    Given установлен формат даты "ГГГГ-ММ-ДДTЧЧ:ММ:СС"
    Given установлен идентификатор пользователя "urn:mock:autotest, urn:mock:system"
    When кликнуть на строку 1 в таблице "/mock-gateway/v1/tariffs/recommended"
    Then ответ является валидным JSON
    Given установлен идентификатор запроса "новый UUID для расчета"
    Given установлен идентификатор пользователя "процент 0.8, лимит 1000000"
    When кликнуть на строку 1 в таблице "/mock-gateway/v1/calculation/profitability"
    Then ответ является валидным JSON
    Then ответ является валидным JSON
    When кликнуть на строку 1 в таблице "/mock-gateway/v1/reports/by-uid"
    Then ответ является валидным JSON
    When кликнуть на строку 1 в таблице "/mock-gateway/v1/reports/by-id"
    When повторить последний запрос 60 раз
    Then ответ является валидным JSON
    Given установлен формат даты "первый день текущего месяца плюс 1 год"
    Then ответ является валидным JSON
    Then ответ является валидным JSON
    Then ответ является валидным JSON
