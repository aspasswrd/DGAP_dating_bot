LIKE_FROM_EVERYONE_QUERY = '''
-- Находим всех пользователей противоположного пола
WITH opposite_gender_users AS (
    SELECT user_id
    FROM bot.users
    WHERE is_male != (SELECT is_male FROM bot.users WHERE user_id = 701459202)
)
-- Для каждого из них добавляем лайк в таблицу match
INSERT INTO bot.match (user_id_1, user_id_2, first_to_second, second_to_first)
SELECT
    LEAST(ogu.user_id, 701459202) AS user_id_1,
    GREATEST(ogu.user_id, 701459202) AS user_id_2,
    CASE
        WHEN ogu.user_id < 701459202 THEN true  -- лайк от противоположного пользователя
        ELSE false
    END AS first_to_second,
    CASE
        WHEN ogu.user_id > 701459202 THEN true  -- лайк от противоположного пользователя
        ELSE false
    END AS second_to_first
FROM opposite_gender_users ogu
ON CONFLICT (user_id_1, user_id_2)
DO UPDATE SET
    first_to_second = EXCLUDED.first_to_second,
    second_to_first = EXCLUDED.second_to_first;
'''

from src.config import get_db_connection

# Функция для пролайкивания всех пользователей противоположного пола
async def like_opposite_gender_users(user_id):
    conn = await get_db_connection()

    try:
        # Получаем пол текущего пользователя (предполагается, что поле 'is_male' хранит информацию о поле)
        user_data = await conn.fetchrow('SELECT is_male FROM bot.users WHERE user_id = $1', user_id)

        if not user_data:
            print(f"Пользователь с ID {user_id} не найден.")
            return

        user_is_male = user_data['is_male']

        # Заменяем placeholder для пола
        opposite_gender = 'true' if not user_is_male else 'false'

        # Выполняем запрос, который создает лайки для всех пользователей противоположного пола
        await conn.execute(LIKE_FROM_EVERYONE_QUERY, user_id, opposite_gender)

        print(f"Пользователь с ID {user_id} пролайкал всех пользователей противоположного пола.")

    except Exception as e:
        print(f"Ошибка: {e}")

    finally:
        await conn.close()


user_id = int(input("Введите ID пользователя, который будет пролайкать всех пользователей противоположного пола: "))

import asyncio

asyncio.run(like_opposite_gender_users(user_id))
