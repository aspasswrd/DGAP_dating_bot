CREATE schema IF NOT EXISTS bot;

CREATE EXTENSION IF NOT EXISTS postgis ;

COMMIT;

DROP TABLE bot.users;

CREATE TABLE IF NOT EXISTS bot.users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(32) NOT NULL,
    name VARCHAR(50) NOT NULL,
    is_male BOOLEAN NOT NULL,
    age INT NOT NULL CHECK (age BETWEEN 14 AND 100),
    location geography(Point, 4326) NOT NULL
);

DROP TABLE bot.preferences;

CREATE TABLE IF NOT EXISTS bot.preferences (
    user_id BIGINT PRIMARY KEY REFERENCES bot.users(user_id) ON DELETE CASCADE,
    min_age INT NOT NULL CHECK (min_age BETWEEN 14 AND 100),
    max_age INT NOT NULL CHECK (max_age BETWEEN 14 AND 100),
    search_radius INT NOT NULL CHECK (search_radius BETWEEN 1 AND 1000), -- в километрах
    CONSTRAINT age_range CHECK (min_age <= max_age)
);

DROP TABLE bot.photos;

CREATE TABLE IF NOT EXISTS bot.photos (
    photo_id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES bot.users(user_id) ON DELETE CASCADE,
    photo BYTEA
);

DROP TABLE bot.match;

CREATE TABLE IF NOT EXISTS bot.match (
    user_id_1 BIGINT NOT NULL REFERENCES bot.users(user_id) ON DELETE CASCADE,
    user_id_2 BIGINT NOT NULL REFERENCES bot.users(user_id) ON DELETE CASCADE,
    first_to_second BOOLEAN NOT NULL DEFAULT false,
    second_to_first BOOLEAN NOT NULL DEFAULT false,
    PRIMARY KEY (user_id_1, user_id_2),
    CHECK (user_id_1 < user_id_2) -- Гарантия уникальности пар
);

CREATE INDEX users_location_gix ON bot.users USING GIST (location);

COMMIT;
