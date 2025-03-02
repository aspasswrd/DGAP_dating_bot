import random
import string
import asyncio
from faker import Faker
from PIL import Image
import io

from src.config import get_db_connection


# Генерация случайного имени пользователя
def generate_random_username():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


# Генерация случайного имени
def generate_random_name():
    fake = Faker()
    return fake.name()


# Генерация случайного возраста
def generate_random_age():
    return random.randint(14, 30)


# Генерация случайного пола
def generate_random_is_male():
    return random.choice([True, False])


# Генерация случайной географической точки (широта, долгота)
def generate_random_location():
    # Параметры случайного места
    lat = random.uniform(55.9, 56)
    lon = random.uniform(37.5, 37.55)
    return f"POINT({lon} {lat})"


# Генерация случайных предпочтений
def generate_random_preferences():
    min_age = 14
    max_age = random.randint(min_age, 30)
    search_radius = random.randint(1, 50)  # В радиусе 1-50 км
    return min_age, max_age, search_radius


# Генерация случайных фото (создаем случайное изображение с использованием Pillow)
def generate_random_photo():
    # Создаем изображение 100x100 пикселей с случайными цветами
    img = Image.new('RGB', (300, 300), color=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))

    # Сохраняем изображение в байтовый поток
    byte_io = io.BytesIO()
    img.save(byte_io, 'PNG')

    # Возвращаем байты изображения
    return byte_io.getvalue()


# Асинхронное подключение и вставка пользователя в базу данных
async def insert_user(conn, user_id, username, name, is_male, age, location):
    await conn.execute('''
        INSERT INTO bot.users(user_id, username, name, is_male, age, location)
        VALUES($1, $2, $3, $4, $5, ST_GeogFromText($6))
    ''', user_id, username, name, is_male, age, location)


# Асинхронная вставка предпочтений пользователя
async def insert_preferences(conn, user_id, min_age, max_age, search_radius):
    await conn.execute('''
        INSERT INTO bot.preferences(user_id, min_age, max_age, search_radius)
        VALUES($1, $2, $3, $4)
    ''', user_id, min_age, max_age, search_radius)


# Асинхронная вставка фото пользователя
async def insert_photo(conn, user_id, photo):
    await conn.execute('''
        INSERT INTO bot.photos(user_id, photo)
        VALUES($1, $2)
    ''', user_id, photo)


# Генерация и вставка случайных пользователей
async def generate_and_insert_users(n):
    # Подключаемся к базе данных
    conn = await get_db_connection()

    for _ in range(n):
        user_id = random.randint(1000000000, 9999999999)
        username = generate_random_username()
        name = generate_random_name()
        is_male = generate_random_is_male()
        age = generate_random_age()
        location = generate_random_location()

        # Вставка пользователя в таблицу
        await insert_user(conn, user_id, username, name, is_male, age, location)

        # Генерация и вставка предпочтений
        min_age, max_age, search_radius = generate_random_preferences()
        await insert_preferences(conn, user_id, min_age, max_age, search_radius)

        # Вставка случайного фото
        photo = generate_random_photo()
        await insert_photo(conn, user_id, photo)

    # Закрытие соединения с базой данных
    user_id = 701459202
    username = 'aspasswrd'
    name = 'Ванек2005'
    is_male = True
    age = 20
    location = generate_random_location()
    photo = generate_random_photo()

    min_age, max_age, search_radius = generate_random_preferences()

    await insert_user(conn, user_id, username, name, is_male, age, location)
    await insert_preferences(conn, user_id, min_age, max_age, search_radius)
    await insert_photo(conn, user_id, photo)
    await conn.close()


# Запуск генерации 10 пользователей
async def main():
    await generate_and_insert_users(1500)


# Запуск асинхронного кода
if __name__ == '__main__':
    asyncio.run(main())
