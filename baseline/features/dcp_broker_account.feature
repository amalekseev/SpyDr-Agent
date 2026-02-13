Feature: Dcp Broker Account

  Scenario: Загрузка нового счета и его отмена
    When Отправить сообщение в кафку "kafka_mock" в топик "MOCK-INCOMING-ACCOUNT" из файла "data/kafka_templates/mock_account.xml"
    When выполнить SELECT запрос в базу "postgres_mock_raw":
      """
      Выполнение SELECT запроса в базу "postgres_mock_raw":
      выбрать из таблицы mock_raw.raw_internal_account запись, где status = 5, owner_id = 10000000001, account_id = accountIdentifier, account_name = accountNumber, account_currency = currencyCode, bank_acc_code = bankCode, owner_brief = 'MOCK_OWNER', institution_brief = 'MOCK_INST' (последняя запись, отсортированная по id desc, limit 1).
      """
    Then результат запроса содержит данные:
      """
      Проверка что результат содержит данные:
      account_type = 'MOCK_TYPE', source_id = 'CD', is_open = 1, oper_type = 'U', account_open_date = openDate 00:00:00, account_close_date = closeDate 00:00:00.
      """
    Then ID вставленной записи сохранен в переменную "recordIdFirst"
    When выполнить SELECT запрос в базу "postgres_mock_raw":
      """
      Выполнение SELECT запроса в базу "postgres_mock_raw":
      посчитать количество записей в таблице mock_raw.raw_internal_account_agreement, где raw_internal_account_id = recordIdFirst, agreement_id входит в (firstAgreementId, secondAgreementId), agreement_number входит в (firstAgreementNumber, secondAgreementNumber), agreement_brief = 'MOCK_TYPE', account_rel_type входит в (firstRelationType, secondRelationType), agreement_type входит в (firstContractType, secondContractType).
      """
    Then результат запроса содержит 2 строк
    When выполнить SELECT запрос в базу "postgres_mock_main":
      """
      Выполнение SELECT запроса в базу "postgres_mock_main":
      посчитать количество контрактов и получить account_id из таблицы mock_main.contract, где agreement_number входит в (firstAgreementNumber, secondAgreementNumber), agreement_brief = 'MOCK_TYPE', account_rel_type входит в (firstRelationType, secondRelationType), agreement_type входит в (firstContractType, secondContractType), сгруппированных по account_id.
      """
    Then результат запроса содержит 2 строк
    Then ID вставленной записи сохранен в переменную "linkedAccountId"
    When выполнить SELECT запрос в базу "postgres_mock_main":
      """
      Выполнение SELECT запроса в базу "postgres_mock_main":
      посчитать количество записей в таблице mock_main.account, где source_account_number = accountNumber, open_date = openDate, close_date = closeDate, currency_id = 1, type_id = 1, id = linkedAccountId.
      """
    Then результат запроса содержит 1 строк
    When Отправить сообщение в кафку "kafka_mock" в топик "MOCK-INCOMING-ACCOUNT" из файла "data/kafka_templates/mock_account.xml"
    When выполнить SELECT запрос в базу "postgres_mock_raw":
      """
      Выполнение SELECT запроса в базу "postgres_mock_raw":
      выбрать из таблицы mock_raw.raw_internal_account запись с теми же фильтрами, что и в шаге 3, но дополнительно: oper_type = 'D', is_open = 0 (0::bit).
      """
    Then результат запроса содержит данные:
      """
      Проверка что результат содержит данные:
      account_type = 'MOCK_TYPE', source_id = 'CD', is_open = 0, oper_type = 'D', account_open_date = openDate 00:00:00, account_close_date = closeDate (текущая дата) 00:00:00.
      """
    Then ID вставленной записи сохранен в переменную "recordIdSecond"
    When выполнить SELECT запрос в базу "postgres_mock_raw":
      """
      Выполнение SELECT запроса в базу "postgres_mock_raw":
      посчитать количество записей в таблице mock_raw.raw_internal_account_agreement, где raw_internal_account_id = recordIdSecond, с теми же фильтрами по договорам, что и в шаге 5.
      """
    Then результат запроса содержит 2 строк
    When выполнить SELECT запрос в базу "postgres_mock_main":
      """
      Выполнение SELECT запроса в базу "postgres_mock_main":
      посчитать количество контрактов и получить account_id из таблицы mock_main.contract с теми же фильтрами, что и в шаге 7.
      """
    Then результат запроса содержит 2 строк
    Then ID вставленной записи сохранен в переменную "linkedAccountId"
    When выполнить SELECT запрос в базу "postgres_mock_main":
      """
      Выполнение SELECT запроса в базу "postgres_mock_main":
      посчитать количество записей в таблице mock_main.account с теми же фильтрами, что и в шаге 9, но с closeDate = текущая дата.
      """
    Then результат запроса содержит 1 строк
