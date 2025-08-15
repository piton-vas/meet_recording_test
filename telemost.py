"""Тестовый скрипт для записи конференции в Яндекс Телемост."""

import os
import time
from pathlib import Path
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
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
    
    # Для запуска на сервере
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    
    # Дополнительные опции для стабильности
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-notifications")

    return chrome_options


def setup_download_directory():
    """Создание и настройка директории для загрузок."""
    download_path = Path(os.getenv("DOWNLOAD_PATH", DEFAULT_DOWNLOAD_PATH))
    download_path.mkdir(parents=True, exist_ok=True)
    return str(download_path.absolute())


def main():
    """Основная функция для записи конференции."""
    # Загрузка переменных окружения
    load_dotenv()

    # Получение настроек
    telemost_url = os.getenv("TELEMOST_URL")
    user_name = os.getenv("USER_NAME", DEFAULT_USER_NAME)
    record_time = int(os.getenv("RECORD_TIME", str(DEFAULT_RECORD_TIME)))

    if not telemost_url:
        logger.error("URL конференции не указан в .env файле")
        return

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

        # Инициализация драйвера
        driver_path = ChromeDriverManager().install()
        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, 20)

        try:
            # Переход на страницу конференции
            logger.info(f"Переход на страницу конференции: {telemost_url}")
            driver.get(telemost_url)

            # Нажатие на кнопку "Продолжить в браузере"
            continue_button = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[contains(@class, 'continueInBrowserButton')]"
                    )
                )
            )
            continue_button.click()
            logger.info("Нажата кнопка 'Продолжить в браузере'")

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
