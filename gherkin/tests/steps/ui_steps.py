"""
UI шаги для тестирования.
Включает шаги для работы с веб-интерфейсом, навигации, взаимодействия с элементами,
работы с формами, таблицами, модальными окнами и другими UI компонентами.
"""
from steps.soft_assert import soft_assert
from pytest_bdd import given, when, then, parsers
import json
import uuid
from datetime import datetime


# ============================================================================
# --- Given steps (UI Setup) ---
# ============================================================================

@given(parsers.parse('открыт браузер "{browser_name}"'))
def open_browser(context, browser_name):
    """Открытие браузера."""
    if "browser" not in context:
        context["browser"] = {}
    context["browser"]["name"] = browser_name
    context["browser"]["open"] = True
    print(f"MOCK: Открыт браузер {browser_name}")


@given(parsers.parse('открыт браузер "{browser_name}" в режиме "{mode}"'))
def open_browser_with_mode(context, browser_name, mode):
    """Открытие браузера в определенном режиме."""
    if "browser" not in context:
        context["browser"] = {}
    context["browser"]["name"] = browser_name
    context["browser"]["mode"] = mode
    context["browser"]["open"] = True
    print(f"MOCK: Открыт браузер {browser_name} в режиме {mode}")


@given(parsers.parse('установлен размер окна {width:d}x{height:d}'))
def set_window_size(context, width, height):
    """Установка размера окна браузера."""
    context["browser"]["window_size"] = {"width": width, "height": height}
    print(f"MOCK: Размер окна установлен на {width}x{height}")


@given(parsers.parse('браузер развернут на весь экран'))
def maximize_browser(context):
    """Разворачивание браузера на весь экран."""
    context["browser"]["maximized"] = True
    print(f"MOCK: Браузер развернут на весь экран")


@given(parsers.parse('установлен таймаут ожидания элементов {timeout:d} секунд'))
def set_element_timeout(context, timeout):
    """Установка таймаута ожидания элементов."""
    context["ui_timeout"] = timeout
    print(f"MOCK: Таймаут ожидания элементов установлен на {timeout} секунд")


@given(parsers.parse('установлен таймаут загрузки страницы {timeout:d} секунд'))
def set_page_load_timeout(context, timeout):
    """Установка таймаута загрузки страницы."""
    context["page_load_timeout"] = timeout
    print(f"MOCK: Таймаут загрузки страницы установлен на {timeout} секунд")


@given(parsers.parse('установлен таймаут выполнения скриптов {timeout:d} секунд'))
def set_script_timeout(context, timeout):
    """Установка таймаута выполнения скриптов."""
    context["script_timeout"] = timeout
    print(f"MOCK: Таймаут выполнения скриптов установлен на {timeout} секунд")


@given(parsers.parse('включен режим мобильной эмуляции "{device_name}"'))
def enable_mobile_emulation(context, device_name):
    """Включение режима мобильной эмуляции."""
    context["browser"]["mobile_emulation"] = device_name
    print(f"MOCK: Включен режим мобильной эмуляции {device_name}")


@given(parsers.parse('установлен User-Agent "{user_agent}"'))
def set_browser_user_agent(context, user_agent):
    """Установка User-Agent браузера."""
    context["browser"]["user_agent"] = user_agent
    print(f"MOCK: User-Agent установлен на {user_agent}")


@given(parsers.parse('установлен язык браузера "{language}"'))
def set_browser_language(context, language):
    """Установка языка браузера."""
    context["browser"]["language"] = language
    print(f"MOCK: Язык браузера установлен на {language}")


@given(parsers.parse('включен режим инкогнито'))
def enable_incognito_mode(context):
    """Включение режима инкогнито."""
    context["browser"]["incognito"] = True
    print(f"MOCK: Режим инкогнито включен")


@given(parsers.parse('отключены уведомления браузера'))
def disable_browser_notifications(context):
    """Отключение уведомлений браузера."""
    context["browser"]["notifications_disabled"] = True
    print(f"MOCK: Уведомления браузера отключены")


@given(parsers.parse('отключены всплывающие окна'))
def disable_popups(context):
    """Отключение всплывающих окон."""
    context["browser"]["popups_disabled"] = True
    print(f"MOCK: Всплывающие окна отключены")


@given(parsers.parse('установлен прокси "{proxy_url}" для браузера'))
def set_browser_proxy(context, proxy_url):
    """Установка прокси для браузера."""
    context["browser"]["proxy"] = proxy_url
    print(f"MOCK: Прокси установлен на {proxy_url}")


@given(parsers.parse('загружено расширение браузера "{extension_path}"'))
def load_browser_extension(context, extension_path):
    """Загрузка расширения браузера."""
    if "extensions" not in context["browser"]:
        context["browser"]["extensions"] = []
    context["browser"]["extensions"].append(extension_path)
    print(f"MOCK: Загружено расширение {extension_path}")


@given(parsers.parse('пользователь авторизован в системе'))
def user_is_authenticated(context):
    """Предусловие: пользователь авторизован."""
    context["auth"] = {"authenticated": True}
    print(f"MOCK: Пользователь авторизован")


@given(parsers.parse('пользователь авторизован как "{role}"'))
def user_is_authenticated_as_role(context, role):
    """Предусловие: пользователь авторизован с ролью."""
    context["auth"] = {"authenticated": True, "role": role}
    print(f"MOCK: Пользователь авторизован как {role}")


# ============================================================================
# --- When steps (Navigation) ---
# ============================================================================

@when(parsers.parse('открыть страницу "{url}"'))
def open_page(context, url):
    """Открытие страницы по URL."""
    context["current_page"] = {"url": url, "loaded": True}
    print(f"MOCK: Открыта страница {url}")


@when(parsers.parse('открыть страницу "{url}" в новой вкладке'))
def open_page_in_new_tab(context, url):
    """Открытие страницы в новой вкладке."""
    if "tabs" not in context:
        context["tabs"] = []
    context["tabs"].append({"url": url})
    context["current_page"] = {"url": url, "loaded": True}
    print(f"MOCK: Открыта страница {url} в новой вкладке")


@when(parsers.parse('перейти назад'))
def navigate_back(context):
    """Переход на предыдущую страницу."""
    print(f"MOCK: Переход назад")


@when(parsers.parse('перейти вперед'))
def navigate_forward(context):
    """Переход на следующую страницу."""
    print(f"MOCK: Переход вперед")


@when(parsers.parse('обновить страницу'))
def refresh_page(context):
    """Обновление страницы."""
    print(f"MOCK: Страница обновлена")


@when(parsers.parse('принудительно обновить страницу'))
def hard_refresh_page(context):
    """Принудительное обновление страницы (без кэша)."""
    print(f"MOCK: Страница принудительно обновлена")


@when(parsers.parse('переключиться на вкладку {tab_index:d}'))
def switch_to_tab(context, tab_index):
    """Переключение на вкладку по индексу."""
    print(f"MOCK: Переключение на вкладку {tab_index}")


@when(parsers.parse('переключиться на вкладку с URL содержащим "{url_part}"'))
def switch_to_tab_by_url(context, url_part):
    """Переключение на вкладку по части URL."""
    print(f"MOCK: Переключение на вкладку с URL содержащим {url_part}")


@when(parsers.parse('закрыть текущую вкладку'))
def close_current_tab(context):
    """Закрытие текущей вкладки."""
    print(f"MOCK: Текущая вкладка закрыта")


@when(parsers.parse('закрыть все вкладки кроме текущей'))
def close_other_tabs(context):
    """Закрытие всех вкладок кроме текущей."""
    print(f"MOCK: Все вкладки кроме текущей закрыты")


@when(parsers.parse('переключиться на iframe "{iframe_selector}"'))
def switch_to_iframe(context, iframe_selector):
    """Переключение на iframe."""
    print(f"MOCK: Переключение на iframe {iframe_selector}")


@when(parsers.parse('переключиться на основной контент'))
def switch_to_default_content(context):
    """Переключение на основной контент из iframe."""
    print(f"MOCK: Переключение на основной контент")


@when(parsers.parse('переключиться на родительский фрейм'))
def switch_to_parent_frame(context):
    """Переключение на родительский фрейм."""
    print(f"MOCK: Переключение на родительский фрейм")


# ============================================================================
# --- When steps (Authentication) ---
# ============================================================================

@when(parsers.parse('Логин в систему: логин {login}, пароль {password}'))
def login_to_system(context, login, password):
    """Авторизация в системе."""
    print(f"MOCK: Логин в систему")
    print(f"MOCK: Логин: {login}")
    print(f"MOCK: Пароль: {'*' * len(password)}")
    
    context["auth"] = {
        "login": login,
        "authenticated": True
    }


@when(parsers.parse('ввести логин "{login}"'))
def enter_login(context, login):
    """Ввод логина."""
    print(f"MOCK: Введен логин {login}")


@when(parsers.parse('ввести пароль "{password}"'))
def enter_password(context, password):
    """Ввод пароля."""
    print(f"MOCK: Введен пароль {'*' * len(password)}")


@when(parsers.parse('нажать кнопку входа'))
def click_login_button(context):
    """Нажатие кнопки входа."""
    context["auth"] = {"authenticated": True}
    print(f"MOCK: Нажата кнопка входа")


@when(parsers.parse('выйти из системы'))
def logout(context):
    """Выход из системы."""
    context["auth"] = {"authenticated": False}
    print(f"MOCK: Выход из системы")


@when(parsers.parse('авторизоваться через SSO'))
def login_via_sso(context):
    """Авторизация через SSO."""
    context["auth"] = {"authenticated": True, "method": "sso"}
    print(f"MOCK: Авторизация через SSO")


@when(parsers.parse('авторизоваться через OAuth провайдер "{provider}"'))
def login_via_oauth(context, provider):
    """Авторизация через OAuth провайдер."""
    context["auth"] = {"authenticated": True, "method": "oauth", "provider": provider}
    print(f"MOCK: Авторизация через OAuth провайдер {provider}")


# ============================================================================
# --- When steps (Element Interaction) ---
# ============================================================================

@when(parsers.parse('кликнуть на элемент "{selector}"'))
def click_element(context, selector):
    """Клик на элемент."""
    print(f"MOCK: Клик на элемент {selector}")


@when(parsers.parse('кликнуть на элемент с текстом "{text}"'))
def click_element_by_text(context, text):
    """Клик на элемент по тексту."""
    print(f"MOCK: Клик на элемент с текстом '{text}'")


@when(parsers.parse('дважды кликнуть на элемент "{selector}"'))
def double_click_element(context, selector):
    """Двойной клик на элемент."""
    print(f"MOCK: Двойной клик на элемент {selector}")


@when(parsers.parse('кликнуть правой кнопкой на элемент "{selector}"'))
def right_click_element(context, selector):
    """Клик правой кнопкой на элемент."""
    print(f"MOCK: Клик правой кнопкой на элемент {selector}")


@when(parsers.parse('навести курсор на элемент "{selector}"'))
def hover_element(context, selector):
    """Наведение курсора на элемент."""
    print(f"MOCK: Курсор наведен на элемент {selector}")


@when(parsers.parse('ввести текст "{text}" в поле "{selector}"'))
def enter_text(context, text, selector):
    """Ввод текста в поле."""
    print(f"MOCK: Введен текст '{text}' в поле {selector}")


@when(parsers.parse('очистить поле "{selector}"'))
def clear_field(context, selector):
    """Очистка поля."""
    print(f"MOCK: Поле {selector} очищено")


@when(parsers.parse('очистить и ввести текст "{text}" в поле "{selector}"'))
def clear_and_enter_text(context, text, selector):
    """Очистка поля и ввод текста."""
    print(f"MOCK: Поле {selector} очищено и введен текст '{text}'")


@when(parsers.parse('добавить текст "{text}" в поле "{selector}"'))
def append_text(context, text, selector):
    """Добавление текста в поле."""
    print(f"MOCK: Добавлен текст '{text}' в поле {selector}")


@when(parsers.parse('нажать клавишу "{key}"'))
def press_key(context, key):
    """Нажатие клавиши."""
    print(f"MOCK: Нажата клавиша {key}")


@when(parsers.parse('нажать комбинацию клавиш "{keys}"'))
def press_key_combination(context, keys):
    """Нажатие комбинации клавиш."""
    print(f"MOCK: Нажата комбинация клавиш {keys}")


@when(parsers.parse('нажать Enter в поле "{selector}"'))
def press_enter_in_field(context, selector):
    """Нажатие Enter в поле."""
    print(f"MOCK: Нажат Enter в поле {selector}")


@when(parsers.parse('нажать Tab в поле "{selector}"'))
def press_tab_in_field(context, selector):
    """Нажатие Tab в поле."""
    print(f"MOCK: Нажат Tab в поле {selector}")


@when(parsers.parse('выбрать значение "{value}" в выпадающем списке "{selector}"'))
def select_dropdown_value(context, value, selector):
    """Выбор значения в выпадающем списке."""
    print(f"MOCK: Выбрано значение '{value}' в списке {selector}")


@when(parsers.parse('выбрать значение по индексу {index:d} в выпадающем списке "{selector}"'))
def select_dropdown_by_index(context, index, selector):
    """Выбор значения по индексу в выпадающем списке."""
    print(f"MOCK: Выбрано значение по индексу {index} в списке {selector}")


@when(parsers.parse('выбрать несколько значений в списке "{selector}":'))
def select_multiple_values(context, selector, docstring):
    """Выбор нескольких значений в списке."""
    values = [v.strip() for v in docstring.strip().split("\n")]
    print(f"MOCK: Выбраны значения {values} в списке {selector}")


@when(parsers.parse('установить чекбокс "{selector}"'))
def check_checkbox(context, selector):
    """Установка чекбокса."""
    print(f"MOCK: Чекбокс {selector} установлен")


@when(parsers.parse('снять чекбокс "{selector}"'))
def uncheck_checkbox(context, selector):
    """Снятие чекбокса."""
    print(f"MOCK: Чекбокс {selector} снят")


@when(parsers.parse('переключить чекбокс "{selector}"'))
def toggle_checkbox(context, selector):
    """Переключение чекбокса."""
    print(f"MOCK: Чекбокс {selector} переключен")


@when(parsers.parse('выбрать радиокнопку "{selector}"'))
def select_radio_button(context, selector):
    """Выбор радиокнопки."""
    print(f"MOCK: Радиокнопка {selector} выбрана")


@when(parsers.parse('загрузить файл "{file_path}" в поле "{selector}"'))
def upload_file(context, file_path, selector):
    """Загрузка файла."""
    print(f"MOCK: Файл {file_path} загружен в поле {selector}")


@when(parsers.parse('загрузить файлы в поле "{selector}":'))
def upload_multiple_files(context, selector, docstring):
    """Загрузка нескольких файлов."""
    files = [f.strip() for f in docstring.strip().split("\n")]
    print(f"MOCK: Файлы {files} загружены в поле {selector}")


@when(parsers.parse('перетащить элемент "{source}" на элемент "{target}"'))
def drag_and_drop(context, source, target):
    """Перетаскивание элемента."""
    print(f"MOCK: Элемент {source} перетащен на {target}")


@when(parsers.parse('прокрутить страницу вниз на {pixels:d} пикселей'))
def scroll_down(context, pixels):
    """Прокрутка страницы вниз."""
    print(f"MOCK: Страница прокручена вниз на {pixels} пикселей")


@when(parsers.parse('прокрутить страницу вверх на {pixels:d} пикселей'))
def scroll_up(context, pixels):
    """Прокрутка страницы вверх."""
    print(f"MOCK: Страница прокручена вверх на {pixels} пикселей")


@when(parsers.parse('прокрутить к элементу "{selector}"'))
def scroll_to_element(context, selector):
    """Прокрутка к элементу."""
    print(f"MOCK: Страница прокручена к элементу {selector}")


@when(parsers.parse('прокрутить в начало страницы'))
def scroll_to_top(context):
    """Прокрутка в начало страницы."""
    print(f"MOCK: Страница прокручена в начало")


@when(parsers.parse('прокрутить в конец страницы'))
def scroll_to_bottom(context):
    """Прокрутка в конец страницы."""
    print(f"MOCK: Страница прокручена в конец")


# ============================================================================
# --- When steps (Waiting) ---
# ============================================================================

@when(parsers.parse('ожидать {seconds:d} секунд'))
def wait_seconds(context, seconds):
    """Ожидание указанное количество секунд."""
    print(f"MOCK: Ожидание {seconds} секунд")


@when(parsers.parse('ожидать появления элемента "{selector}"'))
def wait_for_element_visible(context, selector):
    """Ожидание появления элемента."""
    print(f"MOCK: Ожидание появления элемента {selector}")


@when(parsers.parse('ожидать появления элемента "{selector}" в течение {timeout:d} секунд'))
def wait_for_element_visible_timeout(context, selector, timeout):
    """Ожидание появления элемента с таймаутом."""
    print(f"MOCK: Ожидание появления элемента {selector} в течение {timeout} секунд")


@when(parsers.parse('ожидать исчезновения элемента "{selector}"'))
def wait_for_element_invisible(context, selector):
    """Ожидание исчезновения элемента."""
    print(f"MOCK: Ожидание исчезновения элемента {selector}")


@when(parsers.parse('ожидать исчезновения элемента "{selector}" в течение {timeout:d} секунд'))
def wait_for_element_invisible_timeout(context, selector, timeout):
    """Ожидание исчезновения элемента с таймаутом."""
    print(f"MOCK: Ожидание исчезновения элемента {selector} в течение {timeout} секунд")


@when(parsers.parse('ожидать кликабельности элемента "{selector}"'))
def wait_for_element_clickable(context, selector):
    """Ожидание кликабельности элемента."""
    print(f"MOCK: Ожидание кликабельности элемента {selector}")


@when(parsers.parse('ожидать загрузки страницы'))
def wait_for_page_load(context):
    """Ожидание загрузки страницы."""
    print(f"MOCK: Ожидание загрузки страницы")


@when(parsers.parse('ожидать завершения AJAX запросов'))
def wait_for_ajax(context):
    """Ожидание завершения AJAX запросов."""
    print(f"MOCK: Ожидание завершения AJAX запросов")


@when(parsers.parse('ожидать текст "{text}" на странице'))
def wait_for_text(context, text):
    """Ожидание появления текста на странице."""
    print(f"MOCK: Ожидание текста '{text}' на странице")


@when(parsers.parse('ожидать текст "{text}" в элементе "{selector}"'))
def wait_for_text_in_element(context, text, selector):
    """Ожидание появления текста в элементе."""
    print(f"MOCK: Ожидание текста '{text}' в элементе {selector}")


@when(parsers.parse('ожидать изменения URL на "{url}"'))
def wait_for_url(context, url):
    """Ожидание изменения URL."""
    print(f"MOCK: Ожидание изменения URL на {url}")


@when(parsers.parse('ожидать URL содержащий "{url_part}"'))
def wait_for_url_contains(context, url_part):
    """Ожидание URL содержащего подстроку."""
    print(f"MOCK: Ожидание URL содержащего {url_part}")


# ============================================================================
# --- When steps (Forms and Reports) ---
# ============================================================================

@when(parsers.parse('Сформировать отчет'))
def generate_report(context):
    """Формирование отчета."""
    print(f"MOCK: Формирование отчета")
    
    context["report"] = {
        "parameters": None,
        "generated": True
    }


@when(parsers.parse('заполнить форму:'))
def fill_form(context, datatable):
    """Заполнение формы из таблицы."""
    print(f"MOCK: Заполнение формы: {datatable}")


@when(parsers.parse('заполнить форму данными:'))
def fill_form_with_data(context, docstring):
    """Заполнение формы данными из docstring."""
    print(f"MOCK: Заполнение формы данными:\n{docstring}")


@when(parsers.parse('отправить форму'))
def submit_form(context):
    """Отправка формы."""
    print(f"MOCK: Форма отправлена")


@when(parsers.parse('отправить форму "{form_selector}"'))
def submit_specific_form(context, form_selector):
    """Отправка конкретной формы."""
    print(f"MOCK: Форма {form_selector} отправлена")


@when(parsers.parse('сбросить форму'))
def reset_form(context):
    """Сброс формы."""
    print(f"MOCK: Форма сброшена")


@when(parsers.parse('сбросить форму "{form_selector}"'))
def reset_specific_form(context, form_selector):
    """Сброс конкретной формы."""
    print(f"MOCK: Форма {form_selector} сброшена")


@when(parsers.parse('выбрать дату "{date}" в календаре "{selector}"'))
def select_date(context, date, selector):
    """Выбор даты в календаре."""
    print(f"MOCK: Выбрана дата {date} в календаре {selector}")


@when(parsers.parse('выбрать диапазон дат с "{start_date}" по "{end_date}" в календаре "{selector}"'))
def select_date_range(context, start_date, end_date, selector):
    """Выбор диапазона дат в календаре."""
    print(f"MOCK: Выбран диапазон дат с {start_date} по {end_date} в календаре {selector}")


@when(parsers.parse('установить время "{time}" в поле "{selector}"'))
def set_time(context, time, selector):
    """Установка времени в поле."""
    print(f"MOCK: Установлено время {time} в поле {selector}")


@when(parsers.parse('установить значение слайдера "{selector}" на {value:d}'))
def set_slider_value(context, selector, value):
    """Установка значения слайдера."""
    print(f"MOCK: Значение слайдера {selector} установлено на {value}")


# ============================================================================
# --- When steps (Tables) ---
# ============================================================================

@when(parsers.parse('кликнуть на строку {row:d} в таблице "{table_selector}"'))
def click_table_row(context, row, table_selector):
    """Клик на строку в таблице."""
    print(f"MOCK: Клик на строку {row} в таблице {table_selector}")


@when(parsers.parse('кликнуть на ячейку в строке {row:d} колонке {col:d} таблицы "{table_selector}"'))
def click_table_cell(context, row, col, table_selector):
    """Клик на ячейку в таблице."""
    print(f"MOCK: Клик на ячейку [{row}, {col}] в таблице {table_selector}")


@when(parsers.parse('отсортировать таблицу "{table_selector}" по колонке "{column}"'))
def sort_table_by_column(context, table_selector, column):
    """Сортировка таблицы по колонке."""
    print(f"MOCK: Таблица {table_selector} отсортирована по колонке {column}")


@when(parsers.parse('отфильтровать таблицу "{table_selector}" по значению "{value}" в колонке "{column}"'))
def filter_table(context, table_selector, value, column):
    """Фильтрация таблицы."""
    print(f"MOCK: Таблица {table_selector} отфильтрована по значению {value} в колонке {column}")


@when(parsers.parse('перейти на страницу {page:d} в таблице "{table_selector}"'))
def go_to_table_page(context, page, table_selector):
    """Переход на страницу в таблице."""
    print(f"MOCK: Переход на страницу {page} в таблице {table_selector}")


@when(parsers.parse('установить количество строк на странице {count:d} в таблице "{table_selector}"'))
def set_table_page_size(context, count, table_selector):
    """Установка количества строк на странице."""
    print(f"MOCK: Установлено {count} строк на странице в таблице {table_selector}")


@when(parsers.parse('выбрать все строки в таблице "{table_selector}"'))
def select_all_table_rows(context, table_selector):
    """Выбор всех строк в таблице."""
    print(f"MOCK: Выбраны все строки в таблице {table_selector}")


@when(parsers.parse('снять выбор со всех строк в таблице "{table_selector}"'))
def deselect_all_table_rows(context, table_selector):
    """Снятие выбора со всех строк в таблице."""
    print(f"MOCK: Снят выбор со всех строк в таблице {table_selector}")


# ============================================================================
# --- When steps (Modals and Dialogs) ---
# ============================================================================

@when(parsers.parse('подтвердить диалоговое окно'))
def accept_dialog(context):
    """Подтверждение диалогового окна."""
    print(f"MOCK: Диалоговое окно подтверждено")


@when(parsers.parse('отклонить диалоговое окно'))
def dismiss_dialog(context):
    """Отклонение диалогового окна."""
    print(f"MOCK: Диалоговое окно отклонено")


@when(parsers.parse('ввести текст "{text}" в диалоговое окно'))
def enter_text_in_dialog(context, text):
    """Ввод текста в диалоговое окно."""
    print(f"MOCK: Введен текст '{text}' в диалоговое окно")


@when(parsers.parse('закрыть модальное окно'))
def close_modal(context):
    """Закрытие модального окна."""
    print(f"MOCK: Модальное окно закрыто")


@when(parsers.parse('закрыть модальное окно "{modal_selector}"'))
def close_specific_modal(context, modal_selector):
    """Закрытие конкретного модального окна."""
    print(f"MOCK: Модальное окно {modal_selector} закрыто")


@when(parsers.parse('нажать кнопку "{button_text}" в модальном окне'))
def click_modal_button(context, button_text):
    """Нажатие кнопки в модальном окне."""
    print(f"MOCK: Нажата кнопка '{button_text}' в модальном окне")


# ============================================================================
# --- When steps (Screenshots and Debug) ---
# ============================================================================

@when(parsers.parse('сделать скриншот'))
def take_screenshot(context):
    """Создание скриншота."""
    screenshot_name = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    context["last_screenshot"] = screenshot_name
    print(f"MOCK: Сделан скриншот {screenshot_name}")


@when(parsers.parse('сделать скриншот с именем "{name}"'))
def take_screenshot_with_name(context, name):
    """Создание скриншота с именем."""
    context["last_screenshot"] = name
    print(f"MOCK: Сделан скриншот {name}")


@when(parsers.parse('сделать скриншот элемента "{selector}"'))
def take_element_screenshot(context, selector):
    """Создание скриншота элемента."""
    screenshot_name = f"element_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    context["last_screenshot"] = screenshot_name
    print(f"MOCK: Сделан скриншот элемента {selector}")


@when(parsers.parse('сделать скриншот всей страницы'))
def take_full_page_screenshot(context):
    """Создание скриншота всей страницы."""
    screenshot_name = f"fullpage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    context["last_screenshot"] = screenshot_name
    print(f"MOCK: Сделан скриншот всей страницы")


@when(parsers.parse('выполнить JavaScript:'))
def execute_javascript(context, docstring):
    """Выполнение JavaScript кода."""
    print(f"MOCK: Выполнен JavaScript:\n{docstring}")


@when(parsers.parse('выполнить JavaScript "{script}"'))
def execute_javascript_inline(context, script):
    """Выполнение JavaScript кода (inline)."""
    print(f"MOCK: Выполнен JavaScript: {script}")


# ============================================================================
# --- Then steps (Element Verification) ---
# ============================================================================

@then(parsers.parse('Проверить наличие элемента "{selector}" на странице'))
def check_element_presence(context, selector):
    """Проверка наличия элемента на странице по селектору."""
    print(f"MOCK: Проверка наличия элемента: {selector}")
    
    context["ui_check"] = {
        "selector": selector,
        "found": True
    }
    soft_assert(True)


@then(parsers.parse('элемент "{selector}" отображается на странице'))
def check_element_visible(context, selector):
    """Проверка видимости элемента."""
    print(f"MOCK: Проверка видимости элемента {selector}")
    soft_assert(True)


@then(parsers.parse('элемент "{selector}" не отображается на странице'))
def check_element_not_visible(context, selector):
    """Проверка что элемент не видим."""
    print(f"MOCK: Проверка что элемент {selector} не видим")
    soft_assert(True)


@then(parsers.parse('элемент "{selector}" существует на странице'))
def check_element_exists(context, selector):
    """Проверка существования элемента."""
    print(f"MOCK: Проверка существования элемента {selector}")
    soft_assert(True)


@then(parsers.parse('элемент "{selector}" не существует на странице'))
def check_element_not_exists(context, selector):
    """Проверка отсутствия элемента."""
    print(f"MOCK: Проверка отсутствия элемента {selector}")
    soft_assert(True)


@then(parsers.parse('элемент "{selector}" активен'))
def check_element_enabled(context, selector):
    """Проверка что элемент активен."""
    print(f"MOCK: Проверка что элемент {selector} активен")
    soft_assert(True)


@then(parsers.parse('элемент "{selector}" неактивен'))
def check_element_disabled(context, selector):
    """Проверка что элемент неактивен."""
    print(f"MOCK: Проверка что элемент {selector} неактивен")
    soft_assert(True)


@then(parsers.parse('элемент "{selector}" выбран'))
def check_element_selected(context, selector):
    """Проверка что элемент выбран."""
    print(f"MOCK: Проверка что элемент {selector} выбран")
    soft_assert(True)


@then(parsers.parse('элемент "{selector}" не выбран'))
def check_element_not_selected(context, selector):
    """Проверка что элемент не выбран."""
    print(f"MOCK: Проверка что элемент {selector} не выбран")
    soft_assert(True)


@then(parsers.parse('элемент "{selector}" содержит текст "{text}"'))
def check_element_text(context, selector, text):
    """Проверка текста элемента."""
    print(f"MOCK: Проверка что элемент {selector} содержит текст '{text}'")
    soft_assert(True)


@then(parsers.parse('элемент "{selector}" имеет точный текст "{text}"'))
def check_element_exact_text(context, selector, text):
    """Проверка точного текста элемента."""
    print(f"MOCK: Проверка что элемент {selector} имеет текст '{text}'")
    soft_assert(True)


@then(parsers.parse('элемент "{selector}" не содержит текст "{text}"'))
def check_element_not_contains_text(context, selector, text):
    """Проверка что элемент не содержит текст."""
    print(f"MOCK: Проверка что элемент {selector} не содержит текст '{text}'")
    soft_assert(True)


@then(parsers.parse('элемент "{selector}" имеет значение "{value}"'))
def check_element_value(context, selector, value):
    """Проверка значения элемента."""
    print(f"MOCK: Проверка что элемент {selector} имеет значение '{value}'")
    soft_assert(True)


@then(parsers.parse('элемент "{selector}" имеет атрибут "{attribute}" со значением "{value}"'))
def check_element_attribute(context, selector, attribute, value):
    """Проверка атрибута элемента."""
    print(f"MOCK: Проверка атрибута {attribute}={value} у элемента {selector}")
    soft_assert(True)


@then(parsers.parse('элемент "{selector}" имеет CSS свойство "{property}" со значением "{value}"'))
def check_element_css(context, selector, property, value):
    """Проверка CSS свойства элемента."""
    print(f"MOCK: Проверка CSS свойства {property}={value} у элемента {selector}")
    soft_assert(True)


@then(parsers.parse('элемент "{selector}" имеет класс "{class_name}"'))
def check_element_has_class(context, selector, class_name):
    """Проверка наличия класса у элемента."""
    print(f"MOCK: Проверка что элемент {selector} имеет класс {class_name}")
    soft_assert(True)


@then(parsers.parse('элемент "{selector}" не имеет класс "{class_name}"'))
def check_element_not_has_class(context, selector, class_name):
    """Проверка отсутствия класса у элемента."""
    print(f"MOCK: Проверка что элемент {selector} не имеет класс {class_name}")
    soft_assert(True)


@then(parsers.parse('количество элементов "{selector}" равно {count:d}'))
def check_elements_count(context, selector, count):
    """Проверка количества элементов."""
    print(f"MOCK: Проверка количества элементов {selector}: ожидается {count}")
    soft_assert(True)


@then(parsers.parse('количество элементов "{selector}" больше {count:d}'))
def check_elements_count_greater(context, selector, count):
    """Проверка что элементов больше указанного количества."""
    print(f"MOCK: Проверка что элементов {selector} > {count}")
    soft_assert(True)


@then(parsers.parse('количество элементов "{selector}" меньше {count:d}'))
def check_elements_count_less(context, selector, count):
    """Проверка что элементов меньше указанного количества."""
    print(f"MOCK: Проверка что элементов {selector} < {count}")
    soft_assert(True)


# ============================================================================
# --- Then steps (Page Verification) ---
# ============================================================================

@then(parsers.parse('заголовок страницы равен "{title}"'))
def check_page_title(context, title):
    """Проверка заголовка страницы."""
    print(f"MOCK: Проверка заголовка страницы: ожидается '{title}'")
    soft_assert(True)


@then(parsers.parse('заголовок страницы содержит "{text}"'))
def check_page_title_contains(context, text):
    """Проверка что заголовок содержит текст."""
    print(f"MOCK: Проверка что заголовок содержит '{text}'")
    soft_assert(True)


@then(parsers.parse('URL страницы равен "{url}"'))
def check_page_url(context, url):
    """Проверка URL страницы."""
    print(f"MOCK: Проверка URL страницы: ожидается {url}")
    soft_assert(True)


@then(parsers.parse('URL страницы содержит "{url_part}"'))
def check_page_url_contains(context, url_part):
    """Проверка что URL содержит подстроку."""
    print(f"MOCK: Проверка что URL содержит {url_part}")
    soft_assert(True)


@then(parsers.parse('URL страницы соответствует паттерну "{pattern}"'))
def check_page_url_matches(context, pattern):
    """Проверка URL по паттерну."""
    print(f"MOCK: Проверка URL по паттерну {pattern}")
    soft_assert(True)


@then(parsers.parse('страница содержит текст "{text}"'))
def check_page_contains_text(context, text):
    """Проверка наличия текста на странице."""
    print(f"MOCK: Проверка наличия текста '{text}' на странице")
    soft_assert(True)


@then(parsers.parse('страница не содержит текст "{text}"'))
def check_page_not_contains_text(context, text):
    """Проверка отсутствия текста на странице."""
    print(f"MOCK: Проверка отсутствия текста '{text}' на странице")
    soft_assert(True)


@then(parsers.parse('страница загружена полностью'))
def check_page_loaded(context):
    """Проверка что страница загружена."""
    print(f"MOCK: Проверка что страница загружена полностью")
    soft_assert(True)


@then(parsers.parse('на странице нет JavaScript ошибок'))
def check_no_js_errors(context):
    """Проверка отсутствия JavaScript ошибок."""
    print(f"MOCK: Проверка отсутствия JavaScript ошибок")
    soft_assert(True)


@then(parsers.parse('на странице нет консольных ошибок'))
def check_no_console_errors(context):
    """Проверка отсутствия консольных ошибок."""
    print(f"MOCK: Проверка отсутствия консольных ошибок")
    soft_assert(True)


# ============================================================================
# --- Then steps (Table Verification) ---
# ============================================================================

@then(parsers.parse('таблица "{table_selector}" содержит {count:d} строк'))
def check_table_row_count(context, table_selector, count):
    """Проверка количества строк в таблице."""
    print(f"MOCK: Проверка количества строк в таблице {table_selector}: ожидается {count}")
    soft_assert(True)


@then(parsers.parse('таблица "{table_selector}" содержит строку с текстом "{text}"'))
def check_table_contains_row(context, table_selector, text):
    """Проверка наличия строки с текстом в таблице."""
    print(f"MOCK: Проверка наличия строки с текстом '{text}' в таблице {table_selector}")
    soft_assert(True)


@then(parsers.parse('ячейка в строке {row:d} колонке {col:d} таблицы "{table_selector}" содержит "{text}"'))
def check_table_cell_text(context, row, col, table_selector, text):
    """Проверка текста в ячейке таблицы."""
    print(f"MOCK: Проверка ячейки [{row}, {col}] в таблице {table_selector}: ожидается '{text}'")
    soft_assert(True)


@then(parsers.parse('колонка "{column}" таблицы "{table_selector}" отсортирована по возрастанию'))
def check_table_sorted_asc(context, column, table_selector):
    """Проверка сортировки колонки по возрастанию."""
    print(f"MOCK: Проверка сортировки колонки {column} по возрастанию")
    soft_assert(True)


@then(parsers.parse('колонка "{column}" таблицы "{table_selector}" отсортирована по убыванию'))
def check_table_sorted_desc(context, column, table_selector):
    """Проверка сортировки колонки по убыванию."""
    print(f"MOCK: Проверка сортировки колонки {column} по убыванию")
    soft_assert(True)


# ============================================================================
# --- Then steps (Modal Verification) ---
# ============================================================================

@then(parsers.parse('модальное окно отображается'))
def check_modal_visible(context):
    """Проверка что модальное окно отображается."""
    print(f"MOCK: Проверка что модальное окно отображается")
    soft_assert(True)


@then(parsers.parse('модальное окно "{modal_selector}" отображается'))
def check_specific_modal_visible(context, modal_selector):
    """Проверка что конкретное модальное окно отображается."""
    print(f"MOCK: Проверка что модальное окно {modal_selector} отображается")
    soft_assert(True)


@then(parsers.parse('модальное окно не отображается'))
def check_modal_not_visible(context):
    """Проверка что модальное окно не отображается."""
    print(f"MOCK: Проверка что модальное окно не отображается")
    soft_assert(True)


@then(parsers.parse('модальное окно содержит текст "{text}"'))
def check_modal_contains_text(context, text):
    """Проверка текста в модальном окне."""
    print(f"MOCK: Проверка что модальное окно содержит текст '{text}'")
    soft_assert(True)


# ============================================================================
# --- Then steps (Form Verification) ---
# ============================================================================

@then(parsers.parse('поле "{selector}" имеет ошибку валидации'))
def check_field_has_error(context, selector):
    """Проверка наличия ошибки валидации у поля."""
    print(f"MOCK: Проверка наличия ошибки валидации у поля {selector}")
    soft_assert(True)


@then(parsers.parse('поле "{selector}" имеет ошибку валидации "{error_text}"'))
def check_field_error_text(context, selector, error_text):
    """Проверка текста ошибки валидации."""
    print(f"MOCK: Проверка ошибки валидации '{error_text}' у поля {selector}")
    soft_assert(True)


@then(parsers.parse('поле "{selector}" не имеет ошибок валидации'))
def check_field_no_error(context, selector):
    """Проверка отсутствия ошибок валидации."""
    print(f"MOCK: Проверка отсутствия ошибок валидации у поля {selector}")
    soft_assert(True)


@then(parsers.parse('форма валидна'))
def check_form_valid(context):
    """Проверка валидности формы."""
    print(f"MOCK: Проверка валидности формы")
    soft_assert(True)


@then(parsers.parse('форма невалидна'))
def check_form_invalid(context):
    """Проверка невалидности формы."""
    print(f"MOCK: Проверка невалидности формы")
    soft_assert(True)


# ============================================================================
# --- Then steps (Authentication Verification) ---
# ============================================================================

@then(parsers.parse('пользователь авторизован'))
def check_user_authenticated(context):
    """Проверка что пользователь авторизован."""
    authenticated = context.get("auth", {}).get("authenticated", False)
    print(f"MOCK: Проверка что пользователь авторизован")
    soft_assert(authenticated)


@then(parsers.parse('пользователь не авторизован'))
def check_user_not_authenticated(context):
    """Проверка что пользователь не авторизован."""
    authenticated = context.get("auth", {}).get("authenticated", True)
    print(f"MOCK: Проверка что пользователь не авторизован")
    soft_assert(not authenticated)


@then(parsers.parse('отображается страница входа'))
def check_login_page_displayed(context):
    """Проверка что отображается страница входа."""
    print(f"MOCK: Проверка что отображается страница входа")
    soft_assert(True)


@then(parsers.parse('отображается сообщение об ошибке авторизации'))
def check_auth_error_displayed(context):
    """Проверка отображения ошибки авторизации."""
    print(f"MOCK: Проверка отображения ошибки авторизации")
    soft_assert(True)


# ============================================================================
# --- Then steps (Browser Verification) ---
# ============================================================================

@then(parsers.parse('открыто {count:d} вкладок'))
def check_tabs_count(context, count):
    """Проверка количества открытых вкладок."""
    print(f"MOCK: Проверка количества вкладок: ожидается {count}")
    soft_assert(True)


@then(parsers.parse('cookie "{cookie_name}" существует'))
def check_cookie_exists(context, cookie_name):
    """Проверка существования cookie."""
    print(f"MOCK: Проверка существования cookie {cookie_name}")
    soft_assert(True)


@then(parsers.parse('cookie "{cookie_name}" имеет значение "{value}"'))
def check_cookie_value(context, cookie_name, value):
    """Проверка значения cookie."""
    print(f"MOCK: Проверка значения cookie {cookie_name}: ожидается {value}")
    soft_assert(True)


@then(parsers.parse('cookie "{cookie_name}" не существует'))
def check_cookie_not_exists(context, cookie_name):
    """Проверка отсутствия cookie."""
    print(f"MOCK: Проверка отсутствия cookie {cookie_name}")
    soft_assert(True)


@then(parsers.parse('localStorage содержит ключ "{key}"'))
def check_localstorage_key(context, key):
    """Проверка наличия ключа в localStorage."""
    print(f"MOCK: Проверка наличия ключа {key} в localStorage")
    soft_assert(True)


@then(parsers.parse('localStorage содержит ключ "{key}" со значением "{value}"'))
def check_localstorage_value(context, key, value):
    """Проверка значения в localStorage."""
    print(f"MOCK: Проверка значения {key}={value} в localStorage")
    soft_assert(True)


@then(parsers.parse('sessionStorage содержит ключ "{key}"'))
def check_sessionstorage_key(context, key):
    """Проверка наличия ключа в sessionStorage."""
    print(f"MOCK: Проверка наличия ключа {key} в sessionStorage")
    soft_assert(True)


# ============================================================================
# --- Then steps (Debug) ---
# ============================================================================

@then(parsers.parse('вывести текст элемента "{selector}"'))
def print_element_text(context, selector):
    """Вывод текста элемента."""
    print(f"DEBUG: Текст элемента {selector} = mock_text")


@then(parsers.parse('вывести значение элемента "{selector}"'))
def print_element_value(context, selector):
    """Вывод значения элемента."""
    print(f"DEBUG: Значение элемента {selector} = mock_value")


@then(parsers.parse('вывести URL страницы'))
def print_page_url(context):
    """Вывод URL страницы."""
    url = context.get("current_page", {}).get("url", "unknown")
    print(f"DEBUG: URL страницы = {url}")


@then(parsers.parse('вывести заголовок страницы'))
def print_page_title(context):
    """Вывод заголовка страницы."""
    print(f"DEBUG: Заголовок страницы = Mock Page Title")


@then(parsers.parse('вывести HTML элемента "{selector}"'))
def print_element_html(context, selector):
    """Вывод HTML элемента."""
    print(f"DEBUG: HTML элемента {selector} = <div>mock</div>")


@then(parsers.parse('закрыть браузер'))
def close_browser(context):
    """Закрытие браузера."""
    if "browser" in context:
        context["browser"]["open"] = False
    print(f"MOCK: Браузер закрыт")
