Feature: Dcp Broker Account

  @kafka @db @account @create
  Scenario: Загрузка нового счета и его отмена

    Given установлено подключение к Kafka кластеру "kafka_mock"
    Given установлено подключение к базе данных "postgres_mock_raw"
    Given установлено подключение к базе данных "postgres_mock_main"
    Given загружена конфигурация из файла "data/kafka_templates/mock_account.xml"
    Given подготовлен тестовый контекст

    # Часть 1: Создание счета
    When присвоить переменной "accountIdentifier" случайное число от 60000000000 до 69999999999
    When присвоить переменной "accountNumber" случайное число от 10000000000000 до 19999999999999
    When Присвоить переменной "currencyCode" значение "CUR"
    When присвоить переменной "openDate" дату 1 дней назад
    When присвоить переменной "closeDate" дату через 1 дней
    When Присвоить переменной "bankCode" значение "${accountNumber}"
    When присвоить переменной "firstAgreementId" случайное число от 100000000000 до 199999999999
    When присвоить переменной "secondAgreementId" случайное число от 100000000000 до 199999999999
    When Присвоить переменной "firstAgreementNumber" значение "${firstAgreementId}"
    When Присвоить переменной "secondAgreementNumber" значение "${secondAgreementId}"
    When присвоить переменной "firstRelationType" значение "TYPE_{first_rel_type_4}_{first_rel_type_2}"
    When присвоить переменной "secondRelationType" значение "TYPE_{second_rel_type_4}_{second_rel_type_2}"
    When присвоить переменной "firstContractType" случайную строку длиной 6
    When присвоить переменной "secondContractType" случайную строку длиной 6
    # Генерируем first_rel_type_4 и second_rel_type_4 (4 цифры)
    When присвоить переменной "first_rel_type_4" случайное число от 1000 до 9999
    When присвоить переменной "second_rel_type_4" случайное число от 1000 до 9999
    # Генерируем first_rel_type_2 и second_rel_type_2 (2 цифры)
    When присвоить переменной "first_rel_type_2" случайное число от 10 до 99
    When присвоить переменной "second_rel_type_2" случайное число от 10 до 99
    When Присвоить переменной "firstRelationType" значение "TYPE_${first_rel_type_4}_${first_rel_type_2}"
    When Присвоить переменной "secondRelationType" значение "TYPE_${second_rel_type_4}_${second_rel_type_2}"
    When Присвоить переменной "firstContractType" значение "A${first_contract_digits}"
    When присвоить переменной "first_contract_digits" случайное число от 10000 до 99999
    When Присвоить переменной "secondContractType" значение "B${second_contract_digits}"
    When присвоить переменной "second_contract_digits" случайное число от 10000 до 99999

    When Отправить сообщение в кафку "kafka_mock" в топик "MOCK-INCOMING-ACCOUNT" из файла "data/kafka_templates/mock_account.xml"
    
    # Ожидаем появления записи в raw
    When выполнить SELECT запрос в базу "postgres_mock_raw":
      """
      SELECT *
      FROM mock_raw.raw_internal_account
      WHERE status = 5
        AND owner_id = 10000000001
        AND account_id = ${accountIdentifier}
        AND account_name = ${accountNumber}
        AND account_currency = 'CUR'
        AND bank_acc_code = ${bankCode}
        AND owner_brief = 'MOCK_OWNER'
        AND institution_brief = 'MOCK_INST'
      ORDER BY id DESC
      LIMIT 1
      """
    Then результат запроса содержит данные в течение 120 секунд

    Then результат запроса содержит значение "MOCK_TYPE" в колонке "account_type"
    Then результат запроса содержит значение "CD" в колонке "source_id"
    Then результат запроса содержит значение "1" в колонке "is_open"
    Then результат запроса содержит значение "U" в колонке "oper_type"
    Then результат запроса содержит значение "${openDate} 00:00:00" в колонке "account_open_date"
    Then результат запроса содержит значение "${closeDate} 00:00:00" в колонке "account_close_date"
    Then значение колонки "id" из первой строки сохранено в переменную "recordIdFirst"

    # Проверяем запись договоров
    When выполнить SELECT запрос в базу "postgres_mock_raw":
      """
      SELECT *
      FROM mock_raw.raw_internal_account_agreement
      WHERE raw_internal_account_id = ${recordIdFirst}
        AND agreement_id IN (${firstAgreementId}, ${secondAgreementId})
        AND agreement_number IN (${firstAgreementNumber}, ${secondAgreementNumber})
        AND agreement_brief = 'MOCK_TYPE'
        AND account_rel_type IN ('${firstRelationType}', '${secondRelationType}')
        AND agreement_type IN ('${firstContractType}', '${secondContractType}')
      """
    Then результат запроса содержит данные в течение 60 секунд
    Then результат запроса содержит 2 строк

    # Проверяем контракты контрагента
    When выполнить SELECT запрос в базу "postgres_mock_main":
      """
      SELECT account_id, count(*) as cnt
      FROM mock_main.contract
      WHERE agreement_number IN (${firstAgreementNumber}, ${secondAgreementNumber})
        AND agreement_brief = 'MOCK_TYPE'
        AND account_rel_type IN ('${firstRelationType}', '${secondRelationType}')
        AND agreement_type IN ('${firstContractType}', '${secondContractType}')
      GROUP BY account_id
      """
    Then результат запроса содержит данные в течение 60 секунд
    Then результат запроса содержит 2 строк
    Then значение колонки "account_id" из первой строки сохранено в переменную "linkedAccountId"

    # Проверяем данные счета
    When выполнить SELECT запрос в базу "postgres_mock_main":
      """
      SELECT count(*)
      FROM mock_main.account
      WHERE source_account_number = ${accountNumber}
        AND open_date = '${openDate}'
        AND close_date = '${closeDate}'
        AND currency_id = 1
        AND type_id = 1
        AND id = ${linkedAccountId}
      """
    Then результат запроса содержит данные в течение 60 секунд
    Then результат запроса содержит 1 строк

    # Часть 2: Закрытие счета
    When Присвоить переменной "operationType" значение "D"
    When Присвоить переменной "isOpenFlag" значение "false"
    When присвоить переменной "closeDate" текущую дату в формате "yyyy-MM-dd"
    When Отправить сообщение в кафку "kafka_mock" в топик "MOCK-INCOMING-ACCOUNT" из файла "data/kafka_templates/mock_account.xml"

    # Ожидаем появления обновленной записи в raw с oper_type D
    When выполнить SELECT запрос в базу "postgres_mock_raw":
      """
      SELECT *
      FROM mock_raw.raw_internal_account
      WHERE status = 5
        AND owner_id = 10000000001
        AND account_id = ${accountIdentifier}
        AND account_name = ${accountNumber}
        AND account_currency = 'CUR'
        AND bank_acc_code = ${bankCode}
        AND owner_brief = 'MOCK_OWNER'
        AND institution_brief = 'MOCK_INST'
        AND oper_type = 'D'
        AND is_open = 0
      ORDER BY id DESC
      LIMIT 1
      """
    Then результат запроса содержит данные в течение 120 секунд

    Then результат запроса содержит значение "MOCK_TYPE" в колонке "account_type"
    Then результат запроса содержит значение "CD" в колонке "source_id"
    Then результат запроса содержит значение "0" в колонке "is_open"
    Then результат запроса содержит значение "D" в колонке "oper_type"
    Then результат запроса содержит значение "${openDate} 00:00:00" в колонке "account_open_date"
    Then результат запроса содержит значение "${closeDate} 00:00:00" в колонке "account_close_date"
    Then значение колонки "id" из первой строки сохранено в переменную "recordIdSecond"

    # Проверяем договоры (после закрытия)
    When выполнить SELECT запрос в базу "postgres_mock_raw":
      """
      SELECT *
      FROM mock_raw.raw_internal_account_agreement
      WHERE raw_internal_account_id = ${recordIdSecond}
        AND agreement_id IN (${firstAgreementId}, ${secondAgreementId})
        AND agreement_number IN (${firstAgreementNumber}, ${secondAgreementNumber})
        AND agreement_brief = 'MOCK_TYPE'
        AND account_rel_type IN ('${firstRelationType}', '${secondRelationType}')
        AND agreement_type IN ('${firstContractType}', '${secondContractType}')
      """
    Then результат запроса содержит данные в течение 60 секунд
    Then результат запроса содержит 2 строк

    # Проверяем что контракты не утерялись
    When выполнить SELECT запрос в базу "postgres_mock_main":
      """
      SELECT account_id, count(*) as cnt
      FROM mock_main.contract
      WHERE agreement_number IN (${firstAgreementNumber}, ${secondAgreementNumber})
        AND agreement_brief = 'MOCK_TYPE'
        AND account_rel_type IN ('${firstRelationType}', '${secondRelationType}')
        AND agreement_type IN ('${firstContractType}', '${secondContractType}')
      GROUP BY account_id
      """
    Then результат запроса содержит данные в течение 60 секунд
    Then результат запроса содержит 2 строк
    Then значение колонки "account_id" из первой строки сохранено в переменную "linkedAccountId"
    Then переменная "linkedAccountId" существует

    # Проверяем обновление записи счета
    When выполнить SELECT запрос в базу "postgres_mock_main":
      """
      SELECT count(*)
      FROM mock_main.account
      WHERE source_account_number = ${accountNumber}
        AND open_date = '${openDate}'
        AND close_date = '${closeDate}'
        AND currency_id = 1
        AND type_id = 1
        AND id = ${linkedAccountId}
      """
    Then результат запроса содержит данные в течение 60 секунд
    Then результат запроса содержит 1 строк

    Then тест завершен успешно
