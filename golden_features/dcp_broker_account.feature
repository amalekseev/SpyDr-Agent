@integration @account
Feature: Загрузка нового счета и его отмена
  Проверка загрузки нового счета и его создания в базе данных

  Scenario: Загрузка нового счета и его отмена
    # Инициализация переменных для нового счета
    When Присвоить переменной "accountIdentifier" значение "6${UNIC_NUMBER(10)}"
    When Присвоить переменной "accountNumber" значение "1-00-0${UNIC_NUMBER(11)}"
    When Присвоить переменной "currencyCode" значение "CUR"
    When Присвоить переменной "openDate" значение "${CUR_DATE(%Y-%m-%d)[-1d]}"
    When Присвоить переменной "closeDate" значение "${CUR_DATE(%Y-%m-%d)[+1d]}"
    When Присвоить переменной "bankCode" значение "${accountNumber}"
    When Присвоить переменной "firstAgreementId" значение "01${UNIC_NUMBER(10)}"
    When Присвоить переменной "secondAgreementId" значение "01${UNIC_NUMBER(10)}"
    When Присвоить переменной "firstAgreementNumber" значение "${firstAgreementId}"
    When Присвоить переменной "secondAgreementNumber" значение "${secondAgreementId}"
    When Присвоить переменной "firstRelationType" значение "TYPE_${UNIC_NUMBER(4)}_${UNIC_NUMBER(2)}"
    When Присвоить переменной "secondRelationType" значение "TYPE_${UNIC_NUMBER(4)}_${UNIC_NUMBER(2)}"
    When Присвоить переменной "firstContractType" значение "A${UNIC_NUMBER(5)}"
    When Присвоить переменной "secondContractType" значение "B${UNIC_NUMBER(5)}"

    # Отправка сообщения о создании счета в Kafka
    When Отправить сообщение в кафку "kafka_mock" в топик "MOCK-INCOMING-ACCOUNT" из файла "data/kafka_templates/mock_account.xml"

    # Проверка создания записи в сырых данных
    When Выполнить запрос в базу "postgres_mock_raw"
      """sql
        select id, account_type, source_id, is_open, oper_type, account_open_date, account_close_date
        from mock_raw.raw_internal_account
        where status = 5
        and owner_id = 10000000001
        and account_id = ${accountIdentifier}
        and account_name like '${accountNumber}'
        and account_currency like '${currencyCode}'
        and bank_acc_code like '${bankCode}'
        and owner_brief like 'MOCK_OWNER'
        and institution_brief like 'MOCK_INST'
        order by 1 desc
        limit 1;
      """
    Then Проверить результат запроса из базы "postgres_mock_raw" в течение 120 секунд
      | id               | account_type | source_id | is_open | oper_type | account_open_date     | account_close_date     |
      | ${recordIdFirst} | MOCK_TYPE    | CD        | 1       | U         | ${openDate} 00:00:00  | ${closeDate} 00:00:00  |

    # Проверка связанных договоров
    When Выполнить запрос в базу "postgres_mock_raw"
      """sql
        select count(*) as count_agreements
        from mock_raw.raw_internal_account_agreement
        where raw_internal_account_id = ${recordIdFirst}
        and agreement_id in ('${firstAgreementId}', '${secondAgreementId}')
        and agreement_number in ('${firstAgreementNumber}', '${secondAgreementNumber}')
        and agreement_brief = 'MOCK_TYPE'
        and account_rel_type in ('${firstRelationType}', '${secondRelationType}')
        and agreement_type in ('${firstContractType}', '${secondContractType}');
      """
    Then Проверить результат запроса из базы "postgres_mock_raw" в течение 60 секунд
      | count_agreements |
      | 2                |

    # Проверка публикации контрактов
    When Выполнить запрос в базу "postgres_mock_main"
      """sql
        select count(*) as count_contracts, account_id
        from mock_main.contract c
        where agreement_number in ('${firstAgreementNumber}', '${secondAgreementNumber}')
        and agreement_brief = 'MOCK_TYPE'
        and account_rel_type in ('${firstRelationType}', '${secondRelationType}')
        and agreement_type in ('${firstContractType}', '${secondContractType}')
        group by account_id;
      """
    Then Проверить результат запроса из базы "postgres_mock_main" в течение 60 секунд
      | count_contracts | account_id          |
      | 2               | ${linkedAccountId}  |

    # Проверка создания счета
    When Выполнить запрос в базу "postgres_mock_main"
      """sql
        select count(*) as count_accounts
        from mock_main.account ac
        where ac.source_account_number like '${accountNumber}'
        and ac.open_date = '${openDate}'
        and ac.close_date = '${closeDate}'
        and ac.currency_id = 1
        and ac.type_id = 1
        and ac.id = ${linkedAccountId}
      """
    Then Проверить результат запроса из базы "postgres_mock_main" в течение 60 секунд
      | count_accounts |
      | 1              |

    # Закрытие счета
    When Присвоить переменной "operationType" значение "D"
    When Присвоить переменной "isOpenFlag" значение "false"
    When Присвоить переменной "closeDate" значение "${CUR_DATE(%Y-%m-%d)}"

    When Отправить сообщение в кафку "kafka_mock" в топик "MOCK-INCOMING-ACCOUNT" из файла "data/kafka_templates/mock_account.xml"

    # Проверка закрытия в сырых данных
    When Выполнить запрос в базу "postgres_mock_raw"
      """sql
        select id, account_type, source_id, is_open, oper_type, account_open_date, account_close_date
        from mock_raw.raw_internal_account
        where status = 5
        and owner_id = 10000000001
        and account_id = ${accountIdentifier}
        and account_name like '${accountNumber}'
        and account_currency like '${currencyCode}'
        and bank_acc_code like '${bankCode}'
        and owner_brief like 'MOCK_OWNER'
        and institution_brief like 'MOCK_INST'
        and oper_type like 'D'
        and is_open = 0::bit
        order by 1 desc
        limit 1;
      """
    Then Проверить результат запроса из базы "postgres_mock_raw" в течение 120 секунд
      | id                | account_type | source_id | is_open | oper_type | account_open_date    | account_close_date    |
      | ${recordIdSecond} | MOCK_TYPE    | CD        | 0       | D         | ${openDate} 00:00:00 | ${closeDate} 00:00:00 |

    # Проверка договоров после закрытия
    When Выполнить запрос в базу "postgres_mock_raw"
      """sql
        select count(*) as count_agreements
        from mock_raw.raw_internal_account_agreement
        where raw_internal_account_id = ${recordIdSecond}
        and agreement_id in ('${firstAgreementId}', '${secondAgreementId}')
        and agreement_number in ('${firstAgreementNumber}', '${secondAgreementNumber}')
        and agreement_brief = 'MOCK_TYPE'
        and account_rel_type in ('${firstRelationType}', '${secondRelationType}')
        and agreement_type in ('${firstContractType}', '${secondContractType}');
      """
    Then Проверить результат запроса из базы "postgres_mock_raw" в течение 60 секунд
      | count_agreements |
      | 2                |

    # Проверка контрактов после закрытия
    When Выполнить запрос в базу "postgres_mock_main"
      """sql
        select count(*) as count_contracts, account_id
        from mock_main.contract c
        where agreement_number in ('${firstAgreementNumber}', '${secondAgreementNumber}')
        and agreement_brief = 'MOCK_TYPE'
        and account_rel_type in ('${firstRelationType}', '${secondRelationType}')
        and agreement_type in ('${firstContractType}', '${secondContractType}')
        group by account_id;
      """
    Then Проверить результат запроса из базы "postgres_mock_main" в течение 60 секунд
      | count_contracts | account_id         |
      | 2               | ${linkedAccountId} |

    # Проверка счета после закрытия
    When Выполнить запрос в базу "postgres_mock_main"
      """sql
        select count(*) as count_accounts
        from mock_main.account ac
        where ac.source_account_number like '${accountNumber}'
        and ac.open_date = '${openDate}'
        and ac.close_date = '${closeDate}'
        and ac.currency_id = 1
        and ac.type_id = 1
        and ac.id = ${linkedAccountId}
      """
    Then Проверить результат запроса из базы "postgres_mock_main" в течение 60 секунд
      | count_accounts |
      | 1              |
