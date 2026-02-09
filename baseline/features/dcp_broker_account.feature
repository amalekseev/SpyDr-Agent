Feature: Dcp Broker Account

  @kafka @database @account
  Scenario: Загрузка нового счета и его отмена

    Given установлено подключение к Kafka кластеру "kafka_mock"
    Given установлено подключение к базе данных "postgres_mock_raw"
    Given установлено подключение к базе данных "postgres_mock_main"

    # Генерация уникальных переменных для счета
    When присвоить переменной "accountIdentifier" значение "6"
    When присвоить переменной "accountIdentifierSuffix" случайное число от 1000000000 до 9999999999
    When объединить переменные "accountIdentifier" и "accountIdentifierSuffix" в "accountIdentifier"
    When присвоить переменной "accountNumber" значение "1-00-0"
    When присвоить переменной "accountNumberSuffix" случайное число от 10000000000 до 99999999999
    When объединить переменные "accountNumber" и "accountNumberSuffix" в "accountNumber"
    When присвоить переменной "currencyCode" значение "CUR"
    When присвоить переменной "openDate" дату 1 дней назад
    When присвоить переменной "closeDate" дату 1 дней вперед
    When присвоить переменной "bankCode" значение из переменной "accountNumber"
    When присвоить переменной "firstAgreementIdPrefix" значение "01"
    When присвоить переменной "firstAgreementIdSuffix" случайное число от 1000000000 до 9999999999
    When объединить переменные "firstAgreementIdPrefix" и "firstAgreementIdSuffix" в "firstAgreementId"
    When присвоить переменной "secondAgreementIdPrefix" значение "01"
    When присвоить переменной "secondAgreementIdSuffix" случайное число от 1000000000 до 9999999999
    When объединить переменные "secondAgreementIdPrefix" и "secondAgreementIdSuffix" в "secondAgreementId"
    When присвоить переменной "firstAgreementNumber" значение из переменной "firstAgreementId"
    When присвоить переменной "secondAgreementNumber" значение из переменной "secondAgreementId"
    When присвоить переменной "firstRelationTypePrefix" значение "TYPE_"
    When присвоить переменной "firstRelationTypeMid" случайное число от 1000 до 9999
    When присвоить переменной "firstRelationTypePostfix" значение "_"
    When присвоить переменной "firstRelationTypeSuffix" случайное число от 10 до 99
    When объединить переменные "firstRelationTypePrefix" и "firstRelationTypeMid" в "firstRelationTypeTemp1"
    When объединить переменные "firstRelationTypePostfix" и "firstRelationTypeSuffix" в "firstRelationTypeTemp2"
    When объединить переменные "firstRelationTypeTemp1" и "firstRelationTypeTemp2" в "firstRelationType"
    When присвоить переменной "secondRelationTypePrefix" значение "TYPE_"
    When присвоить переменной "secondRelationTypeMid" случайное число от 1000 до 9999
    When присвоить переменной "secondRelationTypePostfix" значение "_"
    When присвоить переменной "secondRelationTypeSuffix" случайное число от 10 до 99
    When объединить переменные "secondRelationTypePrefix" и "secondRelationTypeMid" в "secondRelationTypeTemp1"
    When объединить переменные "secondRelationTypePostfix" и "secondRelationTypeSuffix" в "secondRelationTypeTemp2"
    When объединить переменные "secondRelationTypeTemp1" и "secondRelationTypeTemp2" в "secondRelationType"
    When присвоить переменной "firstContractTypePrefix" значение "A"
    When присвоить переменной "firstContractTypeSuffix" случайное число от 10000 до 99999
    When объединить переменные "firstContractTypePrefix" и "firstContractTypeSuffix" в "firstContractType"
    When присвоить переменной "secondContractTypePrefix" значение "B"
    When присвоить переменной "secondContractTypeSuffix" случайное число от 10000 до 99999
    When объединить переменные "secondContractTypePrefix" и "secondContractTypeSuffix" в "secondContractType"

    # Часть 1: Создание счета
    When Отправить сообщение в кафку "kafka_mock" в топик "MOCK-INCOMING-ACCOUNT" из файла "data/kafka_templates/mock_account.xml"
    # Ожидание появления записи в raw_internal_account с нужными параметрами
    When выполнить SELECT запрос в базу "postgres_mock_raw":
      """
      SELECT id, account_type, source_id, is_open, oper_type, account_open_date, account_close_date
      FROM mock_raw.raw_internal_account
      WHERE status = 5
        AND owner_id = 10000000001
        AND account_id = '{accountIdentifier}'
        AND account_name = '{accountNumber}'
        AND account_currency = '{currencyCode}'
        AND bank_acc_code = '{bankCode}'
        AND owner_brief = 'MOCK_OWNER'
        AND institution_brief = 'MOCK_INST'
      ORDER BY id DESC
      LIMIT 1
      """
    Then результат запроса в базу "postgres_mock_raw" содержит данные в течение 120 секунд
    Then результат запроса содержит 1 строк

    # Проверяем поля первой строки и сохраняем id
    Then результат запроса в первой строке содержит "MOCK_TYPE" в колонке "account_type"
    Then результат запроса в первой строке содержит "CD" в колонке "source_id"
    Then результат запроса в первой строке содержит "1" в колонке "is_open"
    Then результат запроса в первой строке содержит "U" в колонке "oper_type"
    Then результат запроса в первой строке содержит переменную "openDate" в колонке "account_open_date"
    Then результат запроса в первой строке содержит переменную "closeDate" в колонке "account_close_date"
    Then значение колонки "id" из первой строки сохранено в переменную "recordIdFirst"

    # Проверяем создание договоров (agreements) - должно быть их 2 (по двум id)
    When выполнить SELECT запрос в базу "postgres_mock_raw":
      """
      SELECT count(*) AS cnt
      FROM mock_raw.raw_internal_account_agreement
      WHERE raw_internal_account_id = {recordIdFirst}
        AND agreement_id IN ('{firstAgreementId}','{secondAgreementId}')
        AND agreement_number IN ('{firstAgreementNumber}','{secondAgreementNumber}')
        AND agreement_brief = 'MOCK_TYPE'
        AND account_rel_type IN ('{firstRelationType}','{secondRelationType}')
        AND agreement_type IN ('{firstContractType}','{secondContractType}')
      """
    Then результат запроса в базу "postgres_mock_raw" содержит данные в течение 60 секунд
    Then результат запроса в первой строке содержит "2" в колонке "cnt"

    # Проверяем публикацию контрактов в основной базе (postgres_mock_main)
    When выполнить SELECT запрос в базу "postgres_mock_main":
      """
      SELECT count(*) AS cnt, account_id
      FROM mock_main.contract
      WHERE agreement_number IN ('{firstAgreementNumber}','{secondAgreementNumber}')
        AND agreement_brief = 'MOCK_TYPE'
        AND account_rel_type IN ('{firstRelationType}','{secondRelationType}')
        AND agreement_type IN ('{firstContractType}','{secondContractType}')
      GROUP BY account_id
      """
    Then результат запроса в базу "postgres_mock_main" содержит данные в течение 60 секунд
    Then результат запроса в первой строке содержит "2" в колонке "cnt"
    Then значение колонки "account_id" из первой строки сохранено в переменную "linkedAccountId"

    # Проверяем появление счета в основной базе
    When выполнить SELECT запрос в базу "postgres_mock_main":
      """
      SELECT count(*) AS cnt
      FROM mock_main.account
      WHERE source_account_number = '{accountNumber}'
        AND open_date = '{openDate}'
        AND close_date = '{closeDate}'
        AND currency_id = 1
        AND type_id = 1
        AND id = {linkedAccountId}
      """
    Then результат запроса в базу "postgres_mock_main" содержит данные в течение 60 секунд
    Then результат запроса в первой строке содержит "1" в колонке "cnt"

    # Часть 2: Закрытие счета
    When присвоить переменной "operationType" значением "D"
    When присвоить переменной "isOpenFlag" значением "false"
    When присвоить переменной "currentDate" текущую дату в формате "yyyy-MM-dd"
    When присвоить переменной "closeDate" значением из переменной "currentDate"
    When Отправить сообщение в кафку "kafka_mock" в топик "MOCK-INCOMING-ACCOUNT" из файла "data/kafka_templates/mock_account.xml"

    # Ожидание закрытия счета в raw
    When выполнить SELECT запрос в базу "postgres_mock_raw":
      """
      SELECT id, account_type, source_id, is_open, oper_type, account_open_date, account_close_date
      FROM mock_raw.raw_internal_account
      WHERE status = 5
        AND owner_id = 10000000001
        AND account_id = '{accountIdentifier}'
        AND account_name = '{accountNumber}'
        AND account_currency = '{currencyCode}'
        AND bank_acc_code = '{bankCode}'
        AND owner_brief = 'MOCK_OWNER'
        AND institution_brief = 'MOCK_INST'
        AND oper_type = 'D'
        AND is_open = 0::bit
      ORDER BY id DESC
      LIMIT 1
      """
    Then результат запроса в базу "postgres_mock_raw" содержит данные в течение 120 секунд
    Then результат запроса содержит 1 строк

    # Проверяем поля закрытого счета и сохраняем id
    Then результат запроса в первой строке содержит "MOCK_TYPE" в колонке "account_type"
    Then результат запроса в первой строке содержит "CD" в колонке "source_id"
    Then результат запроса в первой строке содержит "0" в колонке "is_open"
    Then результат запроса в первой строке содержит "D" в колонке "oper_type"
    Then результат запроса в первой строке содержит переменную "openDate" в колонке "account_open_date"
    Then результат запроса в первой строке содержит переменную "closeDate" в колонке "account_close_date"
    Then значение колонки "id" из первой строки сохранено в переменную "recordIdSecond"

    # Проверяем договора после закрытия счета
    When выполнить SELECT запрос в базу "postgres_mock_raw":
      """
      SELECT count(*) AS cnt
      FROM mock_raw.raw_internal_account_agreement
      WHERE raw_internal_account_id = {recordIdSecond}
        AND agreement_id IN ('{firstAgreementId}','{secondAgreementId}')
        AND agreement_number IN ('{firstAgreementNumber}','{secondAgreementNumber}')
        AND agreement_brief = 'MOCK_TYPE'
        AND account_rel_type IN ('{firstRelationType}','{secondRelationType}')
        AND agreement_type IN ('{firstContractType}','{secondContractType}')
      """
    Then результат запроса в базу "postgres_mock_raw" содержит данные в течение 60 секунд
    Then результат запроса в первой строке содержит "2" в колонке "cnt"

    # Проверяем контракты после закрытия счета
    When выполнить SELECT запрос в базу "postgres_mock_main":
      """
      SELECT count(*) AS cnt, account_id
      FROM mock_main.contract
      WHERE agreement_number IN ('{firstAgreementNumber}','{secondAgreementNumber}')
        AND agreement_brief = 'MOCK_TYPE'
        AND account_rel_type IN ('{firstRelationType}','{secondRelationType}')
        AND agreement_type IN ('{firstContractType}','{secondContractType}')
      GROUP BY account_id
      """
    Then результат запроса в базу "postgres_mock_main" содержит данные в течение 60 секунд
    Then результат запроса в первой строке содержит "2" в колонке "cnt"
    Then результат запроса в первой строке содержит переменную "linkedAccountId" в колонке "account_id"

    # Проверяем обновление счета в основной базе с новой датой закрытия
    When выполнить SELECT запрос в базу "postgres_mock_main":
      """
      SELECT count(*) AS cnt
      FROM mock_main.account
      WHERE source_account_number = '{accountNumber}'
        AND open_date = '{openDate}'
        AND close_date = '{closeDate}'
        AND currency_id = 1
        AND type_id = 1
        AND id = {linkedAccountId}
      """
    Then результат запроса в базу "postgres_mock_main" содержит данные в течение 60 секунд
    Then результат запроса в первой строке содержит "1" в колонке "cnt"

    Then тест завершен успешно
