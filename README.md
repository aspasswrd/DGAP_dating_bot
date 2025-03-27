# 🚀 ФОПФ.Знакомства

Телеграм-бот для знакомств на базе aiogram 3.18 с использованием PostgreSQL и PostGIS.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Alpha Version](https://img.shields.io/badge/version-0.1.0--alpha-orange)](https://github.com/aspasswrd/DGAP_dating_bot/releases/tag/v0.1.0-alpha)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.18-green)](https://aiogram.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-blue)](https://postgresql.org)


![dgap_cat](https://i.imgur.com/NX2BCna.jpeg)

## 📌 Особенности
- Асинхронная архитектура
- Геопоиск с использованием PostGIS
- Система лайков/дизлайков
- Личный кабинет с фотографиями
- Гибкие настройки поиска
- Каскадное удаление данных

## ⚙️ Установка

### Требования
- Python 3.11+
- PostgreSQL 15+
- PostGIS 3.3+
- Telegram Bot Token

### Зависимости
```bash
pip install -r requirements.txt
```

Внимание! Для работы нового скрипта генерации фейковых пользователей некоторые импорты, такие как `aiohttp` и `random`, могут быть необязательными для запуска основного бота, если не требуется использование этой функциональности.

### Настройка окружения
Создайте файл `.env` в корне проекта:
```ini
BOT_TOKEN =
DB_HOST=localhost
DB_PORT=5432
DB_USER=
DB_PASSWORD=
DB_NAME=
IMGUR_CLIENT_ID=
```

## 🏃 Запуск
1. Инициализация БД:
```bash
psql -U postgres -f ddl.sql
```

2. Запуск бота:
```bash
python3 bot.py
```

Для генерации фейковых пользователей используйте следующий скрипт:
```bash
python3 user_generator.py
```

Для получения лайков от всех пользователей противоположного пола для заданного пользователя, выполните следующий скрипт:

```bash
python3 fake_likes.py
```

Этот скрипт подключается к базе данных и исполняет запрос, который пролайкает всех пользователей противоположного пола для указанного пользователя. Вам нужно будет ввести ID пользователя, который будет выполнять операцию.

## 🗂 Структура проекта
```
.
├── bot.py
├── user_generator.py         # Скрипт для генерации фейковых пользователей
├── fake_likes.py             # Скрипт для лайков от всех пользователей противоположного пола
├── ddl.sql
├── requirements.txt
├── documentation/            # Документация
├── dml/                      # DML-запросы
├── csv/                      # CSV-файлы с данными аналогичными DML
└── src/
    ├── handlers/      # Обработчики сообщений
    ├── keyboards/     # Клавиатуры
    ├── database/      # Запросы к БД
    └── states/        # Конечные автоматы
```

## 🛠 Функционал
- [x] Регистрация профиля
- [x] Загрузка фотографий
- [x] Геолокация
- [x] Поиск по параметрам
- [x] Система лайков
- [x] Удаление профиля
- [ ] Чат между совпавшими
