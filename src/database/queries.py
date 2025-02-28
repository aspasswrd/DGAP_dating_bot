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
SELECT 
    u.*,
    ST_Distance(
        u.location::geography, 
        (SELECT location::geography FROM bot.users WHERE user_id = $1)
    ) / 1000 AS distance_km
FROM bot.users u
JOIN bot.preferences p ON u.user_id = p.user_id
LEFT JOIN bot.match m ON 
    (u.user_id = m.user_id_1 AND m.user_id_2 = $1) OR 
    (u.user_id = m.user_id_2 AND m.user_id_1 = $1)
WHERE 
    u.user_id != $1 AND
    u.age BETWEEN (SELECT min_age FROM bot.preferences WHERE user_id = $1) AND 
                   (SELECT max_age FROM bot.preferences WHERE user_id = $1) AND
    ST_DWithin(
        u.location::geography,
        (SELECT location::geography FROM bot.users WHERE user_id = $1),
        (SELECT search_radius * 1000 FROM bot.preferences WHERE user_id = $1)
    )
ORDER BY RANDOM()
LIMIT 10;
'''

DELETE_USER_QUERY = '''
                DELETE FROM bot.users WHERE user_id = $1
                '''

INSERT_USER_QUERY = '''
                INSERT INTO bot.users(user_id, username, name, is_male, age, location)
                VALUES($1, $2, $3, $4, $5, ST_GeogFromText($6))
                '''

INSERT_USER_PHOTO_QUERY = '''
                INSERT INTO bot.photos(user_id, photo)
                VALUES($1, $2)
                '''

INSERT_USER_PREFERENCES_QUERY = '''
                INSERT INTO bot.preferences(user_id, min_age, max_age, search_radius)
                VALUES($1, $2, $3, $4)
                '''

UPDATE_USER_PREFERENCES_QUERY = '''
                UPDATE bot.preferences
                SET min_age = $2, max_age = $3, search_radius = $4
                WHERE user_id = $1
                '''
