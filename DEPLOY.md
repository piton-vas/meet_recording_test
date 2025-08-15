# Инструкция по развертыванию на Ubuntu сервере

## Подготовка сервера

1. Подключитесь к серверу по SSH:
```bash
ssh username@your_server_ip
```

2. Обновите пакеты:
```bash
sudo apt update
sudo apt upgrade -y
```

3. Установите необходимые пакеты:
```bash
# Установка Python и инструментов разработки
sudo apt install -y python3.10 python3.10-venv python3-pip

# Установка Chrome и зависимостей
sudo apt install -y wget curl unzip xvfb
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
rm google-chrome-stable_current_amd64.deb
```

## Установка приложения

1. Создайте директорию для приложения:
```bash
mkdir -p /opt/meet_recording_test
cd /opt/meet_recording_test
```

2. Склонируйте репозиторий:
```bash
git clone [URL репозитория] .
```

3. Создайте и активируйте виртуальное окружение:
```bash
python3.10 -m venv .venv
source .venv/bin/activate
```

4. Установите зависимости:
```bash
pip install -r requirements.txt
```

5. Создайте и настройте файл конфигурации:
```bash
cp .env.example .env
nano .env  # Отредактируйте параметры
```

## Настройка Selenium в headless режиме

Для работы Selenium на сервере без графического интерфейса, добавьте следующие опции в файл `telemost.py` в функцию `setup_chrome_options()`:

```python
# Добавьте эти опции в начало функции setup_chrome_options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
```

## Настройка прав доступа

1. Создайте системного пользователя:
```bash
sudo useradd -r -s /bin/false telemost
```

2. Установите права на директорию:
```bash
sudo chown -R telemost:telemost /opt/meet_recording_test
sudo chmod -R 755 /opt/meet_recording_test
```

## Создание systemd сервиса

1. Создайте файл сервиса:
```bash
sudo nano /etc/systemd/system/telemost.service
```

2. Добавьте следующее содержимое:
```ini
[Unit]
Description=Telemost Recording Service
After=network.target

[Service]
Type=simple
User=telemost
Group=telemost
WorkingDirectory=/opt/meet_recording_test
Environment=PYTHONPATH=/opt/meet_recording_test
ExecStart=/opt/meet_recording_test/.venv/bin/python telemost.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. Активируйте и запустите сервис:
```bash
sudo systemctl daemon-reload
sudo systemctl enable telemost
sudo systemctl start telemost
```

## Мониторинг и логи

1. Проверка статуса сервиса:
```bash
sudo systemctl status telemost
```

2. Просмотр логов:
```bash
# Логи systemd
sudo journalctl -u telemost -f

# Логи приложения
tail -f /opt/meet_recording_test/logs/telemost_*.log
```

## Обновление приложения

1. Остановите сервис:
```bash
sudo systemctl stop telemost
```

2. Обновите код:
```bash
cd /opt/meet_recording_test
sudo -u telemost git pull
```

3. Обновите зависимости:
```bash
sudo -u telemost .venv/bin/pip install -r requirements.txt
```

4. Запустите сервис:
```bash
sudo systemctl start telemost
```

## Устранение неполадок

1. Если Chrome не запускается:
```bash
# Проверьте, что Chrome установлен
google-chrome --version

# Проверьте наличие необходимых библиотек
ldd $(which google-chrome)

# Установите недостающие библиотеки
sudo apt install -y libnss3 libgconf-2-4
```

2. Если возникают проблемы с правами:
```bash
# Проверьте права на директории
ls -la /opt/meet_recording_test

# Проверьте права на виртуальное окружение
ls -la /opt/meet_recording_test/.venv

# При необходимости исправьте права
sudo chown -R telemost:telemost /opt/meet_recording_test
```

3. Если сервис не запускается:
```bash
# Проверьте детальные логи
sudo journalctl -u telemost -n 100 --no-pager
```

## Рекомендации по безопасности

1. Настройте файрвол:
```bash
sudo ufw enable
sudo ufw allow ssh
```

2. Регулярно обновляйте систему:
```bash
sudo apt update
sudo apt upgrade -y
```

3. Настройте ротацию логов:
```bash
sudo nano /etc/logrotate.d/telemost
```

Добавьте:
```
/opt/meet_recording_test/logs/telemost_*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 telemost telemost
}
```
