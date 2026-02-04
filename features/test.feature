Feature: Проверка логирования и захвата вывода

  Scenario: Создание лог-записи и проверка вывода
    Given I create log records for the following categories
    And I create a log record with:
      | category | root |
      | level    | ERROR |
      | message  | Test Error |
    When I capture log records
    Then the command output should contain "CAPTURED LOG:"
    And the command output should contain "ERROR:root: Test Error"