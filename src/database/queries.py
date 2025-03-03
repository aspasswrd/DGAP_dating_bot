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

GET_STACK_QUERY = '''
WITH user_preferences AS (
    SELECT
        p.min_age,
        p.max_age,
        p.search_radius,
        u.is_male,
        u.location AS user_location
    FROM bot.preferences p
    JOIN bot.users u USING(user_id)
    WHERE p.user_id = $1
),
matching_users AS (
    SELECT
        u.user_id,
        u.username,
        u.name,
        u.is_male,
        u.age,
        ST_Distance(up.user_location, u.location) / 1000 AS distance_km
    FROM bot.users u
    JOIN user_preferences up
    ON u.age BETWEEN up.min_age AND up.max_age
    AND ST_DWithin(up.user_location, u.location, up.search_radius * 1000)
    AND u.user_id != $1
    AND u.is_male != up.is_male
    AND NOT EXISTS (
        SELECT 1
        FROM bot.match m
        WHERE (m.user_id_1 = $1 AND m.user_id_2 = u.user_id AND m.first_to_second IS NULL)
        OR (m.user_id_1 = u.user_id AND m.user_id_2 = $1 AND m.second_to_first IS NULL)
    )
)
SELECT
    mu.user_id,
    mu.username,
    mu.name,
    mu.is_male,
    mu.age,
    mu.distance_km
FROM matching_users mu
ORDER BY random()
LIMIT 10;
'''

GET_MATCHES_QUERY = '''
SELECT 
    u.user_id, 
    u.username, 
    mu.name, 
    mu.age, 
    dm.user_id_with AS matched_user_id,
    mu.username AS matched_username
FROM bot.done_match dm
JOIN bot.users u ON dm.user_id = u.user_id
JOIN bot.users mu ON dm.user_id_with = mu.user_id
WHERE dm.user_id = $1
ORDER BY u.user_id
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
