# 🚀 ФОПФ.Знакомства

Телеграм-бот для знакомств на базе aiogram 3.18 с использованием PostgreSQL и PostGIS

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.18-green)](https://aiogram.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-blue)](https://postgresql.org)

![dgap_cat](dgap.jpg)

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

### Настройка окружения
Создайте файл `.env` в корне проекта:
```ini
BOT_TOKEN=ваш_токен_бота
DB_HOST=localhost
DB_PORT=5432
DB_USER=ваш_юзер
DB_PASSWORD=ваш_пароль
DB_NAME=название_бд
```

## 🏃 Запуск
1. Инициализация БД:
```bash
psql -U postgres -f init.sql
```

2. Запуск бота:
```bash
python bot.py
```

## 🗂 Структура проекта
```
.
├── bot.py
├── init.sql
├── requirements.txt
└── src/
    ├── handlers/      # Обработчики сообщений
    ├── keyboards/     # Клавиатуры
    ├── database/      # Модели и запросы к БД
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
- [ ] Премиум-функции
