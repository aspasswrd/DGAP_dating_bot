SELECT_USER_QUERY = '''
                SELECT u.*, p.min_age, p.max_age, p.search_radius
                FROM bot.users u
                JOIN bot.preferences p ON u.user_id = p.user_id
                WHERE u.user_id = $1
                '''

CHECK_USER_QUERY = '''
                SELECT 1 FROM bot.users WHERE user_id = $1
                '''


SELECT_USER_PHOTO_QUERY = '''
                SELECT photo FROM bot.photos WHERE user_id = $1
                '''

FIND_MATCH_QUERY = '''
                SELECT u.* FROM bot.users u
                JOIN bot.preferences p ON u.user_id = p.user_id
                WHERE u.user_id != $1
                AND u.age BETWEEN (SELECT min_age FROM bot.preferences WHERE user_id = $1)
                AND (SELECT max_age FROM bot.preferences WHERE user_id = $1)
                ORDER BY RANDOM()
                LIMIT 1
                '''

DELETE_USER_QUERY = '''
                DELETE FROM bot.users WHERE user_id = $1
                '''

INSERT_USER_QUERY = '''
                INSERT INTO bot.users(user_id, name, is_male, age, location)
                VALUES($1, $2, $3, $4, ST_GeogFromText($5))
                '''

INSERT_USER_PHOTO_QUERY = '''
                INSERT INTO bot.photos(user_id, photo)
                VALUES($1, $2)
                '''

INSERT_USER_PREFERENCES_QUERY = '''
                INSERT INTO bot.preferences(user_id, min_age, max_age, search_radius)
                VALUES($1, $2, $3, $4)
                '''