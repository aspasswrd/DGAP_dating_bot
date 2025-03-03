TRUNCATE bot.users CASCADE;

SELECT * FROM bot.photos;

SELECT * FROM bot.match;


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