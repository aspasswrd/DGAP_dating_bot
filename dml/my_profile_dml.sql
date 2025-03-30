INSERT INTO bot.users
VALUES (701459202, 'aspasswrd', 'Иван', true, 19, '0101000020E6100000E4A3B64FB4CF424082126A37E7DA4B40');

INSERT INTO bot.photos (user_id, photo, valid_from, valid_to)
VALUES (701459202, 'https://i.imgur.com/gQz6k12.jpeg', CURRENT_TIMESTAMP, NULL);

INSERT INTO bot.preferences
VALUES (701459202, 18, 100, 100);