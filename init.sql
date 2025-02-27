CREATE schema IF NOT EXISTS bot;

CREATE EXTENSION IF NOT EXISTS postgis ;

COMMIT;

CREATE TABLE IF NOT EXISTS bot.users (
    user_id BIGINT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    is_male BOOLEAN NOT NULL,
    age INT NOT NULL CHECK (age BETWEEN 14 AND 100),
    location geography(Point, 4326) NOT NULL
);


CREATE TABLE IF NOT EXISTS bot.preferences (
    user_id BIGINT PRIMARY KEY REFERENCES bot.users(user_id) ON DELETE CASCADE,
    min_age INT NOT NULL CHECK (min_age BETWEEN 14 AND 100),
    max_age INT NOT NULL CHECK (max_age BETWEEN 14 AND 100),
    search_radius INT NOT NULL CHECK (search_radius BETWEEN 1 AND 1000), -- в километрах
    CONSTRAINT age_range CHECK (min_age <= max_age)
);

CREATE TABLE IF NOT EXISTS bot.photos (
    photo_id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES bot.users(user_id) ON DELETE CASCADE,
    photo BYTEA
);

CREATE TABLE IF NOT EXISTS bot.likes (
    like_id SERIAL PRIMARY KEY,
    from_user BIGINT REFERENCES bot.users(user_id) ON DELETE CASCADE,
    to_user BIGINT REFERENCES bot.users(user_id) ON DELETE CASCADE,
    UNIQUE(from_user, to_user)
);

COMMIT;
