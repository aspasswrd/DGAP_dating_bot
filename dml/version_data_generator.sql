INSERT INTO bot.photos (user_id, photo, valid_from, valid_to)
WITH random_photos AS (
    SELECT
        user_id,
        photo,
        CURRENT_TIMESTAMP - INTERVAL '1 day' * FLOOR(RANDOM() * 365) AS valid_from,
        CASE
            WHEN RANDOM() < 0.8
            THEN CURRENT_TIMESTAMP - INTERVAL '1 day' * FLOOR(RANDOM() * 365)
        END AS valid_to
    FROM bot.photos
    ORDER BY RANDOM()
    LIMIT 100
)
SELECT
    user_id,
    photo,
    valid_from,
    CASE
        WHEN valid_to < valid_from THEN valid_from + INTERVAL '1 day'
        ELSE valid_to
    END AS valid_to
FROM random_photos;