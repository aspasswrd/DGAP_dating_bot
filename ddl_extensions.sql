CREATE OR REPLACE VIEW bot.active_users_with_photos AS
SELECT u.user_id, u.username, u.name, u.age, u.is_male,
       p.photo, i.interests
FROM bot.users u
JOIN bot.photos p ON u.user_id = p.user_id AND p.valid_to IS NULL
LEFT JOIN (
    SELECT ui.user_id,
           STRING_AGG(i.name, ', ') AS interests
    FROM bot.user_interests ui
    JOIN bot.interests i ON ui.interest_id = i.interest_id
    GROUP BY ui.user_id
) i ON u.user_id = i.user_id;


CREATE OR REPLACE VIEW bot.match_stats AS
SELECT
    u1.user_id AS user1_id,
    u1.name AS user1_name,
    u2.user_id AS user2_id,
    u2.name AS user2_name,
    dm.match_id,
    dm.user_id_with AS matched_with
FROM bot.done_match dm
JOIN bot.users u1 ON dm.user_id = u1.user_id
JOIN bot.users u2 ON dm.user_id_with = u2.user_id;


CREATE INDEX users_location_gix ON bot.users USING GIST (location);
CREATE INDEX idx_users_age_gender ON bot.users(age, is_male);
CREATE INDEX idx_user_interests_interest_id ON bot.user_interests(interest_id);
CREATE UNIQUE INDEX idx_photos_user_current ON bot.photos(user_id) WHERE valid_to IS NULL;


CREATE OR REPLACE PROCEDURE bot.create_user(
    p_user_id BIGINT,
    p_username VARCHAR(32),
    p_name VARCHAR(50),
    p_is_male BOOLEAN,
    p_age INT,
    p_longitude FLOAT,
    p_latitude FLOAT,
    p_photo_url VARCHAR(2048),
    OUT result BOOLEAN
)
LANGUAGE plpgsql
AS $$
BEGIN
    BEGIN
        INSERT INTO bot.users(user_id, username, name, is_male, age, location)
        VALUES(p_user_id, p_username, p_name, p_is_male, p_age,
              ST_GeogFromText('POINT(' || p_longitude || ' ' || p_latitude || ')'));

        INSERT INTO bot.photos (user_id, photo, valid_from, valid_to)
        VALUES (p_user_id, p_photo_url, CURRENT_TIMESTAMP, NULL);

        INSERT INTO bot.preferences(user_id, min_age, max_age, search_radius)
        VALUES(p_user_id,
              GREATEST(p_age - 2, 14),
              LEAST(p_age + 2, 100),
              100);

        result := TRUE;
    EXCEPTION WHEN OTHERS THEN
        result := FALSE;
    END;
END;
$$;


CREATE OR REPLACE FUNCTION bot.find_potential_matches(
    p_user_id BIGINT,
    p_limit INT DEFAULT 10
)
RETURNS TABLE(
    user_id BIGINT,
    username VARCHAR(32),
    name VARCHAR(50),
    is_male BOOLEAN,
    age INT,
    distance_km FLOAT,
    photo_url VARCHAR(2048)
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH user_preferences AS (
        SELECT p.min_age, p.max_age, p.search_radius, u.is_male, u.location AS user_location
        FROM bot.preferences p
        JOIN bot.users u USING(user_id)
        WHERE p.user_id = p_user_id
    )
    SELECT
        u.user_id,
        u.username,
        u.name,
        u.is_male,
        u.age,
        ST_Distance(up.user_location, u.location) / 1000 AS distance_km,
        p.photo AS photo_url
    FROM bot.users u
    JOIN user_preferences up ON u.age BETWEEN up.min_age AND up.max_age
    JOIN bot.photos p ON u.user_id = p.user_id AND p.valid_to IS NULL
    WHERE u.user_id != p_user_id
      AND u.is_male != up.is_male
      AND ST_DWithin(up.user_location, u.location, up.search_radius * 1000)
      AND NOT EXISTS (
          SELECT 1 FROM bot.match m
          WHERE (m.user_id_1 = p_user_id AND m.user_id_2 = u.user_id)
             OR (m.user_id_1 = u.user_id AND m.user_id_2 = p_user_id)
      )
    ORDER BY random()
    LIMIT p_limit;
END;
$$;


CREATE OR REPLACE FUNCTION bot.check_match(
    p_user1_id BIGINT,
    p_user2_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_match_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM bot.match
        WHERE user_id_1 = LEAST(p_user1_id, p_user2_id)
          AND user_id_2 = GREATEST(p_user1_id, p_user2_id)
          AND ((user_id_1 = p_user1_id AND first_to_second = TRUE)
            OR (user_id_2 = p_user1_id AND second_to_first = TRUE))
    ) INTO v_match_exists;

    RETURN v_match_exists;
END;
$$;


CREATE OR REPLACE FUNCTION bot.check_preferences_age()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.min_age > NEW.max_age THEN
        RAISE EXCEPTION 'Минимальный возраст не может быть больше максимального';
    END IF;
    RETURN NEW;
END;
$$;


CREATE TRIGGER trg_check_preferences_age
BEFORE INSERT OR UPDATE ON bot.preferences
FOR EACH ROW
EXECUTE FUNCTION bot.check_preferences_age();


--CREATE OR REPLACE FUNCTION bot.create_default_preferences()
--RETURNS TRIGGER
--LANGUAGE plpgsql
--AS $$
--BEGIN
--    INSERT INTO bot.preferences(user_id, min_age, max_age, search_radius)
--    VALUES(NEW.user_id,
--          GREATEST(NEW.age - 2, 14),
--          LEAST(NEW.age + 2, 100),
--          100);
--    RETURN NEW;
--END;
--$$;


--CREATE TRIGGER trg_create_default_preferences
--AFTER INSERT ON bot.users
--FOR EACH ROW
--EXECUTE FUNCTION bot.create_default_preferences();


CREATE TABLE IF NOT EXISTS bot.deleted_users_log (
    log_id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    username VARCHAR(32),
    name VARCHAR(50) NOT NULL,
    deletion_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE OR REPLACE FUNCTION bot.log_deleted_user()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO bot.deleted_users_log(user_id, username, name)
    VALUES(OLD.user_id, OLD.username, OLD.name);
    RETURN OLD;
END;
$$;


CREATE TRIGGER trg_log_deleted_user
BEFORE DELETE ON bot.users
FOR EACH ROW
EXECUTE FUNCTION bot.log_deleted_user();