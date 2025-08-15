"""Тестовый скрипт для записи конференции в Яндекс Телемост."""

import os
import time
from pathlib import Path
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from loguru import logger

# Значения по умолчанию
DEFAULT_USER_NAME = "Test User"
DEFAULT_RECORD_TIME = 60  # в секундах
DEFAULT_DOWNLOAD_PATH = "downloads"


def setup_chrome_options():
    """Настройка опций Chrome."""
    chrome_options = Options()
    
    # Headless режим для работы без GUI
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Автоматически разрешать доступ к микрофону и камере
    chrome_options.add_argument("--use-fake-ui-for-media-stream")
    chrome_options.add_argument("--use-fake-device-for-media-stream")
    
    # Базовые опции безопасности
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Отключаем GPU
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    
    # Дополнительные опции для стабильности
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-notifications")
    
    # Опции для улучшения производительности
    chrome_options.add_argument("--disable-features=TranslateUI")
    chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    chrome_options.add_argument("--disable-site-isolation-trials")
    chrome_options.add_argument("--disable-web-security")
    
    # Дополнительные опции для стабильности на сервере
    chrome_options.add_argument("--disable-setuid-sandbox")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--disable-background-networking")
    
    # Настройки для более быстрой загрузки
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_setting_values.media_stream_mic": 1,
        "profile.default_content_setting_values.media_stream_camera": 1,
        "profile.default_content_setting_values.geolocation": 2,
    }
    chrome_options.add_experimental_option("prefs", prefs)

    return chrome_options


def setup_download_directory():
    """Создание и настройка директории для загрузок."""
    download_path = Path(os.getenv("DOWNLOAD_PATH", DEFAULT_DOWNLOAD_PATH))
    download_path.mkdir(parents=True, exist_ok=True)
    return str(download_path.absolute())


def validate_env_vars():
    """Проверка и валидация переменных окружения."""
    env_vars = {
        "TELEMOST_URL": {
            "value": os.getenv("TELEMOST_URL"),
            "required": True,
            "error": "URL конференции не указан в .env файле"
        },
        "USER_NAME": {
            "value": os.getenv("USER_NAME", DEFAULT_USER_NAME),
            "required": False
        },
        "RECORD_TIME": {
            "value": os.getenv("RECORD_TIME", str(DEFAULT_RECORD_TIME)),
            "required": False,
            "validator": lambda x: x.isdigit() and int(x) > 0,
            "error": "RECORD_TIME должно быть положительным числом"
        },
        "ENV": {
            "value": os.getenv("ENV", "prod").lower(),
            "required": False,
            "validator": lambda x: x in ["prod", "local"],
            "error": "ENV должно быть 'prod' или 'local'"
        }
    }

    for var_name, config in env_vars.items():
        value = config["value"]
        
        # Проверка обязательных переменных
        if config["required"] and not value:
            logger.error(config["error"])
            return False
            
        # Валидация значения если есть validator
        if value and config.get("validator"):
            if not config["validator"](value):
                logger.error(config["error"])
                return False
    
    return True


def main():
    """Основная функция для записи конференции."""
    # Загрузка переменных окружения
    load_dotenv()

    # Валидация переменных окружения
    if not validate_env_vars():
        return

    # Получение настроек
    telemost_url = os.getenv("TELEMOST_URL")
    user_name = os.getenv("USER_NAME", DEFAULT_USER_NAME)
    record_time = int(os.getenv("RECORD_TIME", str(DEFAULT_RECORD_TIME)))

    try:
        # Настройка логирования
        log_path = Path("logs")
        log_path.mkdir(exist_ok=True)
        logger.add(
            log_path / (
                f"telemost_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            ),
            rotation="1 day"
        )

        # Настройка Chrome
        download_dir = setup_download_directory()
        chrome_options = setup_chrome_options()
        chrome_options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
            }
        )

        # Определяем режим работы
        env_mode = os.getenv("ENV", "prod").lower()
        is_local = env_mode == "local"
        logger.info(f"Режим работы: {'локальный' if is_local else 'production'}")

        if is_local:
            # В локальном режиме используем Chrome for Testing
            logger.info("Используется Chrome for Testing")
            # Опции для локального режима
            chrome_options.add_argument("--allow-insecure-localhost")
            chrome_options.add_argument("--remote-debugging-port=9222")
            # Отключаем headless режим для локальной разработки
            chrome_options.arguments.remove("--headless=new")
            
            # Если указан путь к Chrome for Testing
            chrome_path = os.getenv("CHROME_PATH")
            if chrome_path:
                chrome_options.binary_location = chrome_path
        else:
            # В production используем обычный Chrome
            logger.info("Используется Google Chrome")
            # Дополнительные опции для production режима на Ubuntu
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-software-rasterizer")
            # Дополнительные опции для стабильности на сервере
            chrome_options.add_argument("--disable-setuid-sandbox")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--single-process")
            # Принудительно используем /dev/shm
            chrome_options.add_argument("--disable-dev-shm-usage=false")

        # Проверка наличия Chrome
        if not is_local:
            try:
                import subprocess
                chrome_version = subprocess.check_output(['google-chrome', '--version'])
                logger.info(f"Версия Chrome: {chrome_version.decode().strip()}")
            except Exception as e:
                logger.error(f"Chrome не найден: {str(e)}")
                logger.info("Попытка установить Chrome...")
                try:
                    # Обновляем список пакетов
                    subprocess.run(['sudo', 'apt-get', 'update'], check=True)
                    # Устанавливаем Chrome
                    subprocess.run([
                        'sudo', 'apt-get', 'install', '-y',
                        'google-chrome-stable'
                    ], check=True)
                    logger.info("Chrome успешно установлен")
                except Exception as e:
                    logger.error(f"Не удалось установить Chrome: {str(e)}")
                    raise

        # Инициализация драйвера
        try:
            logger.info("Создание экземпляра драйвера...")
            driver = webdriver.Chrome(options=chrome_options)
            logger.info("Драйвер успешно создан")
        except Exception as e:
            logger.error(f"Ошибка при создании драйвера: {str(e)}")
            if not is_local:
                # Показываем дополнительную информацию на сервере
                try:
                    subprocess.run(['ps', 'aux', '|', 'grep', 'chrome'], shell=True)
                    subprocess.run(['ls', '-la', '/usr/bin/google-chrome'], shell=True)
                except:
                    pass
            raise
        wait = WebDriverWait(driver, 20)

        try:
            # Переход на страницу конференции
            logger.info(f"Переход на страницу конференции: {telemost_url}")
            try:
                driver.get(telemost_url)
                logger.info("Страница успешно загружена")
                
                # Проверяем текущий URL
                current_url = driver.current_url
                logger.info(f"Текущий URL: {current_url}")
                
                # Получаем исходный код страницы для диагностики
                page_source = driver.page_source
                if len(page_source) > 0:
                    logger.info(f"Длина исходного кода страницы: {len(page_source)} символов")
                else:
                    logger.error("Страница пустая!")
                
                # Делаем скриншот для диагностики
                if not is_local:
                    screenshot_path = "error_screenshot.png"
                    driver.save_screenshot(screenshot_path)
                    logger.info(f"Сделан скриншот: {screenshot_path}")
                
                # Ждем появления кнопки с таймаутом
                logger.info("Ожидание кнопки 'Продолжить в браузере'...")
                continue_button = wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            "//button[contains(@class, 'continueInBrowserButton')]"
                        )
                    )
                )
                
                # Проверяем видимость кнопки
                if continue_button.is_displayed():
                    logger.info("Кнопка 'Продолжить в браузере' найдена и видима")
                    continue_button.click()
                    logger.info("Кнопка 'Продолжить в браузере' нажата")
                else:
                    logger.error("Кнопка найдена, но не видима!")
                    
            except Exception as e:
                logger.error(f"Ошибка при загрузке страницы: {str(e)}")
                if not is_local:
                    # Показываем дополнительную информацию на сервере
                    try:
                        import psutil
                        process = psutil.Process()
                        logger.info(f"Использование памяти: {process.memory_info().rss / 1024 / 1024:.2f} MB")
                        logger.info(f"CPU: {process.cpu_percent()}%")
                    except:
                        pass
                raise

            # Ввод имени пользователя
            name_input = wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//input[contains(@class, 'Textinput-Control')]"
                    )
                )
            )
            name_input.clear()
            name_input.send_keys(user_name)
            logger.info(f"Введено имя пользователя: {user_name}")

            # Отключение микрофона и камеры
            for device in ["Выключить микрофон", "Выключить камеру"]:
                button = wait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH, f"//button[@title='{device}']")
                    )
                )
                button.click()
                logger.info(f"Нажата кнопка: {device}")

            # Присоединение к конференции
            join_button = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[contains(@class, 'joinMeetingButton')]"
                    )
                )
            )
            join_button.click()
            logger.info("Присоединение к конференции")

            # Ожидание загрузки интерфейса
            time.sleep(5)

            # Начало записи
            menu_button = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[@title='Ещё']")
                )
            )
            menu_button.click()
            logger.info("Открыто меню 'Ещё'")

            record_button = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//div[@title='Записать на компьютер']")
                )
            )
            record_button.click()
            logger.info("Начата запись")

            # Ожидание заданного времени
            logger.info(f"Ожидание {record_time} секунд...")
            time.sleep(record_time)

            # Остановка записи
            stop_button = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[@title='Остановить запись на компьютер']"
                    )
                )
            )
            stop_button.click()
            logger.info("Запись остановлена")

            # Ожидание скачивания файла
            time.sleep(10)
            logger.info("Тест завершен успешно")

        finally:
            driver.quit()
            logger.info("Браузер закрыт")

    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")


if __name__ == "__main__":
    main()
