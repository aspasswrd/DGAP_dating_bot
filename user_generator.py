import random
import string
import asyncio
import aiohttp
from PIL import Image

from src.config import get_db_connection, upload_image


# Генерация случайного имени пользователя
def generate_random_username():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


# Генерация случайного возраста
def generate_random_age():
    return random.randint(14, 30)

# Генерация случайной географической точки (широта, долгота)
def generate_random_location():
    lat = random.uniform(55.9, 56)
    lon = random.uniform(37.5, 37.55)
    return f"POINT({lon} {lat})"


# Генерация случайных предпочтений
def generate_random_preferences():
    min_age = 14
    max_age = random.randint(min_age, 30)
    search_radius = random.randint(1, 50)
    return min_age, max_age, search_radius

# Асинхронная функция для получения случайного имени и фото из API RandomUser.me
async def get_random_user():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://randomuser.me/api/') as response:
            if response.status == 200:
                data = await response.json()
                user = data['results'][0]
                name = user['name']['first']
                photo_url = user['picture']['large']
                gender = user['gender']
                is_male = False
                if gender == "male":
                    is_male = True
                return name, photo_url, is_male
            else:
                return None, None


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
    conn = await get_db_connection()

    for _ in range(n):
        user_id = random.randint(1000000000, 9999999999)
        username = generate_random_username()
        name, photo_url, is_male = await get_random_user()
        age = generate_random_age()
        location = generate_random_location()

        await insert_user(conn, user_id, username, name, is_male, age, location)

        min_age, max_age, search_radius = generate_random_preferences()
        await insert_preferences(conn, user_id, min_age, max_age, search_radius)

        await insert_photo(conn, user_id, photo_url)

    # Закрытие соединения с базой данных
    await conn.close()


# Запуск генерации пользователей
async def main():
    await generate_and_insert_users(500)


# Запуск асинхронного кода
if __name__ == '__main__':
    asyncio.run(main())
