"""Модуль настройки логгирования для всего проекта."""

import logging
import datetime as dt
import os
import zipfile
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def setup_logging() -> None:
    """Настройка логгирования для всего проекта."""

    # Создаем директорию для логов, если её нет
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Проверяем и исправляем права доступа к файлу логов
    log_file = log_dir / 'main.log'
    if log_file.exists():
        # Проверяем, можем ли мы писать в файл
        if not os.access(log_file, os.W_OK):
            try:
                # Пытаемся удалить файл с неправильными правами
                log_file.unlink()
            except (PermissionError, OSError):
                # Если не можем удалить, используем альтернативное имя файла
                # или пропускаем файловый обработчик и используем только консольный вывод
                import tempfile
                log_file = Path(tempfile.gettempdir()) / 'virtual_assistant_main.log'
                # Если и временный файл недоступен, используем только консоль
                try:
                    # Проверяем, можем ли мы создать файл во временной директории
                    test_file = log_file.parent / '.test_write'
                    test_file.touch()
                    test_file.unlink()
                except (PermissionError, OSError):
                    # Используем только консольный вывод
                    logging.basicConfig(
                        level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler()]
                    )
                    return

    # Настройка обработчика с ротацией по неделям
    try:
        handler = TimedRotatingFileHandler(
            filename=log_file,
            when='W0',  # Ротация по понедельникам (W0 - неделя начинается с понедельника)
            interval=1,
            backupCount=7,
            encoding='utf-8'
        )
    except (PermissionError, OSError):
        # Если не можем создать файловый обработчик, используем консольный
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        return

    # Архивация "пакетом": один архив на неделю, куда складываем все ротированные файлы
    # вида *.log.<YYYY-MM-DD> и удаляем исходники после добавления.
    def _parse_suffix(rotated_path: str) -> str:
        base_name = Path(handler.baseFilename).name  # например "main.log"
        dest_name = Path(rotated_path).name          # например "main.log.2025-12-08"
        prefix = f"{base_name}."
        if dest_name.startswith(prefix):
            return dest_name[len(prefix):]
        # fallback, если вдруг формат изменится
        return dt.datetime.now(dt.UTC).strftime("%Y-%m-%d")

    def _rotator(source: str, dest: str) -> None:
        # 1) Выполняем "обычную" ротацию (переименование текущего файла в dest)
        os.rename(source, dest)

        suffix = _parse_suffix(dest)
        archive_path = log_dir / f"archive-{suffix}.zip"

        # 2) Складываем в один архив все *.log.<suffix> (включая только что созданный dest)
        with zipfile.ZipFile(archive_path, mode="a", compression=zipfile.ZIP_DEFLATED) as zf:
            for p in log_dir.glob(f"*.log.{suffix}"):
                # На всякий случай пропускаем текущий "живой" файл без суффикса.
                if p.name == Path(handler.baseFilename).name:
                    continue
                zf.write(p, arcname=p.name)
                try:
                    p.unlink()
                except OSError:
                    pass

    handler.rotator = _rotator

    # Форматирование логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    # Настройка корневого логгера
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[handler]
    )

# Настройка логгирования при импорте модуля
setup_logging()
