@dcp @broker @account
Feature: Dcp Broker Account

  @load_and_cancel_account
  Scenario: Загрузка нового счета и его отмена
    When заполнить форму данными:
      """
      Сформировать уникальные данные для нового счета:
      - accountIdentifier: "6" + 10 случайных цифр
      - accountNumber: "1-00-0" + 11 случайных цифр
      - currencyCode: "CUR"
      - openDate: вчерашняя дата (формат ГГГГ-ММ-ДД)
      - closeDate: завтрашняя дата (формат ГГГГ-ММ-ДД)
      - bankCode: равен accountNumber
      - firstAgreementId: "01" + 10 случайных цифр
      - secondAgreementId: "01" + 10 случайных цифр
      - firstAgreementNumber: равен firstAgreementId
      - secondAgreementNumber: равен secondAgreementId
      - firstRelationType: "TYPE_" + 4 цифры + "_" + 2 цифры
      - secondRelationType: "TYPE_" + 4 цифры + "_" + 2 цифры
      - firstContractType: "A" + 5 случайных цифр
      - secondContractType: "B" + 5 случайных цифр
      """
    When Отправить сообщение в кафку "kafka_mock" в топик "MOCK-INCOMING-ACCOUNT" из файла "data/kafka_templates/mock_account.xml"
    Then результат запроса в базу "postgres_mock_raw" содержит данные в течение 120 секунд
    Then результат запроса содержит данные:
    Then таблица "mock_raw.raw_internal_account_agreement" в базе "postgres_mock_raw" содержит 2 записей
    Then таблица "mock_main.contract" в базе "postgres_mock_main" содержит 2 записей
    Then таблица "mock_main.account" в базе "postgres_mock_main" содержит 1 записей
    When заполнить форму данными:
      """
      Установить параметры закрытия: operationType = "D", isOpenFlag = "false", closeDate = текущая дата.
      """
    When Отправить сообщение в кафку "kafka_mock" в топик "MOCK-INCOMING-ACCOUNT" из файла "data/kafka_templates/mock_account.xml"
    Then результат запроса в базу "postgres_mock_raw" содержит данные в течение 120 секунд
    Then результат запроса содержит данные:
    Then таблица "mock_raw.raw_internal_account_agreement" в базе "postgres_mock_raw" содержит 2 записей
    Then таблица "mock_main.contract" в базе "postgres_mock_main" содержит 2 записей
    Then таблица "mock_main.account" в базе "postgres_mock_main" содержит 1 записей
