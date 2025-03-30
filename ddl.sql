CREATE SCHEMA IF NOT EXISTS bot;

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS bot.users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(32),
    name VARCHAR(50) NOT NULL,
    is_male BOOLEAN NOT NULL,
    age INT NOT NULL CHECK (age BETWEEN 14 AND 100),
    location geography(Point, 4326) NOT NULL
);

CREATE TABLE IF NOT EXISTS bot.preferences (
    user_id BIGINT PRIMARY KEY REFERENCES bot.users(user_id) ON DELETE CASCADE,
    min_age INT NOT NULL DEFAULT 14 CHECK (min_age BETWEEN 14 AND 100),
    max_age INT NOT NULL DEFAULT 100 CHECK (max_age BETWEEN 14 AND 100),
    search_radius INT NOT NULL DEFAULT 100 CHECK (search_radius <= 20000),
    CONSTRAINT age_range CHECK (min_age <= max_age)
);

CREATE TABLE IF NOT EXISTS bot.photos (
    photo_id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES bot.users(user_id) ON DELETE CASCADE,
    photo VARCHAR(2048) NOT NULL,
    valid_from TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP DEFAULT NULL,
    CONSTRAINT back_to_the_future CHECK (valid_from < valid_to OR valid_to IS NULL)
);

CREATE TABLE IF NOT EXISTS bot.match (
    user_id_1 BIGINT NOT NULL REFERENCES bot.users(user_id) ON DELETE CASCADE,
    user_id_2 BIGINT NOT NULL REFERENCES bot.users(user_id) ON DELETE CASCADE,
    first_to_second BOOLEAN,
    second_to_first BOOLEAN,
    PRIMARY KEY (user_id_1, user_id_2),
    CHECK (user_id_1 < user_id_2)
);

CREATE TABLE IF NOT EXISTS bot.done_match (
    match_id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES bot.users(user_id) ON DELETE CASCADE,
    user_id_with BIGINT NOT NULL,
    CONSTRAINT no_self_match CHECK (user_id <> user_id_with),
    CONSTRAINT unique_match_pair UNIQUE (user_id, user_id_with)
);

CREATE TABLE IF NOT EXISTS bot.interests (
    interest_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS bot.user_interests (
    user_id BIGINT NOT NULL REFERENCES bot.users(user_id) ON DELETE CASCADE,
    interest_id INT NOT NULL REFERENCES bot.interests(interest_id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, interest_id)
);

CREATE INDEX users_location_gix ON bot.users USING GIST (location);
CREATE INDEX idx_preferences_user_id ON bot.preferences(user_id);
CREATE INDEX idx_photos_user_id ON bot.photos(user_id);
CREATE INDEX idx_match_user_ids ON bot.match(user_id_1, user_id_2);
CREATE INDEX idx_done_match_user_id ON bot.done_match(user_id);
CREATE INDEX idx_users_age_gender ON bot.users(age, is_male);
CREATE INDEX idx_match_user1 ON bot.match(user_id_1);
CREATE INDEX idx_match_user2 ON bot.match(user_id_2);
CREATE INDEX idx_done_match_pairs ON bot.done_match(user_id, user_id_with);
CREATE INDEX idx_interests_name ON bot.interests(name);
CREATE INDEX idx_user_interests_interest_id ON bot.user_interests(interest_id);
CREATE UNIQUE INDEX idx_photos_user_current ON bot.photos(user_id) WHERE valid_to IS NULL;