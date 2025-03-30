import random
import asyncio
import aiohttp

from src.config import get_db_connection

def generate_random_age():
    return random.randint(14, 100)

def generate_random_location():
    lat = random.uniform(55.7, 56)
    lon = random.uniform(37.5, 37.7)
    return f"POINT({lon} {lat})"

def generate_random_preferences():
    min_age = random.randint(14, 20)
    max_age = random.randint(45, 100)
    search_radius = 1000
    return min_age, max_age, search_radius

async def get_random_user():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://randomuser.me/api/') as response:
            if response.status == 200:
                data = await response.json()
                user = data['results'][0]
                return (
                    user['name']['first'],
                    user['picture']['large'],
                    user['gender'] == "male",
                    user['login']['username']
                )
            return None, None, None, None


async def get_existing_interests(conn):
    records = await conn.fetch('SELECT interest_id FROM bot.interests')
    return [r['interest_id'] for r in records]


async def insert_user_interests(conn, user_id, interest_ids):
    for interest_id in interest_ids:
        await conn.execute('''
            INSERT INTO bot.user_interests(user_id, interest_id)
            VALUES($1, $2)
            ON CONFLICT DO NOTHING
        ''', user_id, interest_id)


async def generate_matches(conn, user_ids):
    for _ in range(len(user_ids) * 2):
        user1, user2 = sorted(random.sample(user_ids, 2))
        first_to_second = random.choice([True, False, None])
        second_to_first = random.choice([True, False, None]) if first_to_second else None

        await conn.execute('''
            INSERT INTO bot.match(user_id_1, user_id_2, first_to_second, second_to_first)
            VALUES($1, $2, $3, $4)
            ON CONFLICT (user_id_1, user_id_2) DO UPDATE
            SET first_to_second = EXCLUDED.first_to_second,
                second_to_first = EXCLUDED.second_to_first
        ''', user1, user2, first_to_second, second_to_first)


# Генерация и вставка пользователя
async def generate_and_insert_user():
    conn = await get_db_connection()
    user_id = random.randint(1000000000, 9999999999)
    name, photo_url, is_male, username = await get_random_user()

    if not photo_url:
        await conn.close()
        return None

    age = generate_random_age()
    location = generate_random_location()

    # Вставка основных данных
    await conn.execute('''
        INSERT INTO bot.users(user_id, username, name, is_male, age, location)
        VALUES($1, $2, $3, $4, $5, ST_GeogFromText($6))
    ''', user_id, username, name, is_male, age, location)

    # Вставка предпочтений
    min_age, max_age, sr = generate_random_preferences()
    await conn.execute('''
        INSERT INTO bot.preferences(user_id, min_age, max_age, search_radius)
        VALUES($1, $2, $3, $4)
    ''', user_id, min_age, max_age, sr)

    # Вставка фото
    await conn.execute('''
        INSERT INTO bot.photos(user_id, photo)
        VALUES($1, $2)
    ''', user_id, photo_url)

    # Добавление интересов
    interests = await get_existing_interests(conn)
    if interests:
        selected = random.sample(interests, k=random.randint(1, 4))
        await insert_user_interests(conn, user_id, selected)

    print(name)
    await conn.close()
    return user_id


# Пакетная генерация пользователей
async def generate_and_insert_users(n):
    user_ids = []
    tasks = [asyncio.create_task(generate_and_insert_user()) for _ in range(n)]

    for task in asyncio.as_completed(tasks):
        user_id = await task
        if user_id: user_ids.append(user_id)

    conn = await get_db_connection()
    await generate_matches(conn, user_ids)
    await conn.close()


# Основная функция
async def main():
    for i in range(50):
        await generate_and_insert_users(4)

    conn = await get_db_connection()

    await conn.execute('''
        DELETE FROM bot.match
        WHERE first_to_second IS NULL AND second_to_first IS NULL;
    ''')

    await conn.execute('''
        INSERT INTO bot.done_match (user_id, user_id_with)
        SELECT user_id_1, user_id_2 FROM bot.match
        WHERE first_to_second = TRUE AND second_to_first = TRUE
        UNION ALL
        SELECT user_id_2, user_id_1 FROM bot.match
        WHERE first_to_second = TRUE AND second_to_first = TRUE
        ON CONFLICT (user_id, user_id_with) DO NOTHING;
    ''')

    await conn.close()

if __name__ == '__main__':
    asyncio.run(main())