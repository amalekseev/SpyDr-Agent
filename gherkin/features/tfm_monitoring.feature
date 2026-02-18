@monitoring
Feature: Мониторинг сервисов

  Scenario: Проверка статистики сервиса
    When Отправить "GET /service/monitoring/statistics" на REST сервер "app_service"
    Then Проверить ответ с кодом 200 и body
      """json
      {
          "actionTasks": {
              "TaskRegenerate": {
                  "waitingCount": "$[int]"
              }
          }
      }
      """

  Scenario: Проверка загрузки данных из внешнего источника
    When Выполнить запрос в базу "postgres":
      """sql
      DELETE FROM APP_SCHEMA.ACCOUNT_BALANCE where POSITION_ID = '00001'
      """
    And Отправить сообщение в кафку "kafka_app" в топик "APP-TOPIC-ACCOUNTBALANCE"
      """xml
      <record timestamp='2023-01-01T10:00:00.000' exchange='EXCHANGE' market='MKT' system='SYS' entity='ENTITY' interface='API' table='ACCOUNT_BALANCE' POSITION_ID='00001' />
      """
    And Выполнить запрос в базу "postgres":
      """sql
      SELECT * FROM APP_SCHEMA.ACCOUNT_BALANCE WHERE POSITION_ID = '00001'
      """
    Then Проверить результат запроса из базы "postgres" в течение 60 секунд
      | POSITION_ID |
      | 00001       |
