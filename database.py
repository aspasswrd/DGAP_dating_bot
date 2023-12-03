import sqlite3


class dbworker:
    def __init__(self, database_file):
        self.connection = sqlite3.connect(database_file)
        self.cursor = self.connection.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS users(telegram_id INT PRIMARY KEY, telegram_username TEXT, full_name TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS profile_list(telegram_id INT PRIMARY KEY, telegram_username TEXT,"
                            "name TEXT,"
                            "description TEXT,"
                            "city TEXT,"
                            "photo TEXT,"
                            "sex TEXT,"
                            "age INTEGER,"
                            "social_link TEXT)")


    def user_exists(self, user_id):
        '''Проверка есть ли юзер в бд'''
        with self.connection:
            result = self.cursor.execute('SELECT * FROM `users` WHERE `telegram_id` = ?', (user_id,)).fetchall()
            return bool(len(result))

    def add_user(self, telegram_username, telegram_id, full_name):
        '''Добавляем нового юзера'''
        with self.connection:
            return self.cursor.execute(
                "INSERT INTO `users` (`telegram_username`, `telegram_id`,`full_name`) VALUES(?,?,?)",
                (telegram_username, telegram_id, full_name))

    def create_profile(self, telegram_id, telegram_username, name, description, city, photo, sex, age, social_link):
        '''Создаём анкету'''
        with self.connection:
            return self.cursor.execute(
                "INSERT INTO `profile_list` (`telegram_id`,`telegram_username`,`name`,`description`,`city`,`photo`,`sex`,`age`,`social_link`) VALUES(?,?,?,?,?,?,?,?,?)",
                (telegram_id, telegram_username, name, description, city, photo, sex, age, social_link))

    def profile_exists(self, user_id):
        '''Проверка есть ли анкета в бд'''
        with self.connection:
            result = self.cursor.execute('SELECT * FROM `profile_list` WHERE `telegram_id` = ?', (user_id,)).fetchall()
            return bool(len(result))

    def delete_profile(self, user_id):
        '''Удаление анкеты'''
        with self.connection:
            return self.cursor.execute("DELETE FROM `profile_list` WHERE `telegram_id` = ?", (user_id,))

    def all_profile(self, user_id):
        '''поиск по анкетам'''
        with self.connection:
            return self.cursor.execute("SELECT * FROM `profile_list` WHERE `telegram_id` = ?", (user_id,)).fetchall()

    def edit_description(self, description, user_id):
        '''изменение описания'''
        with self.connection:
            return self.cursor.execute('UPDATE `profile_list` SET `description` = ? WHERE `telegram_id` = ?',
                                       (description, user_id))

    def edit_age(self, age, user_id):
        '''изменение возвраста'''
        with self.connection:
            return self.cursor.execute('UPDATE `profile_list` SET `age` = ? WHERE `telegram_id` = ?', (age, user_id))

    def search_profile(self, city, age, sex):
        '''поиск хаты'''
        try:
            if str(sex) == 'мужчина':
                sex_search = 'женщина'
            else:
                sex_search = 'мужчина'
            with self.connection:
                return self.cursor.execute(
                    "SELECT `telegram_id` FROM `profile_list` WHERE `city` = ? AND `sex` = ? ORDER BY `age` DESC",
                    (city, sex_search)).fetchall()
        except Exception as e:
            print(e)

    def get_info(self, user_id):
        '''получение ифнормации по профилю'''
        with self.connection:
            return self.cursor.execute("SELECT * FROM `profile_list` WHERE `telegram_id` = ?", (user_id,)).fetchone()

    def search_profile_status(self, user_id):
        '''возвращение статуса'''
        with self.connection:
            return self.cursor.execute("SELECT `search_id` FROM `users` WHERE `telegram_id` = ?", (user_id,)).fetchone()

    def edit_profile_status(self, user_id, num):
        '''изменение статуса'''
        with self.connection:
            return self.cursor.execute('UPDATE `users` SET `search_id` = ? WHERE `telegram_id` = ?',
                                       (str(num + 1), user_id))

    def edit_zero_profile_status(self, user_id):
        '''изменение статуса на 0 когда анкеты заканчиваются'''
        with self.connection:
            return self.cursor.execute('UPDATE `users` SET `search_id` = 0 WHERE `telegram_id` = ?', (user_id,))

    def get_info_user(self, user_id):
        '''получение информации по юзеру'''
        with self.connection:
            return self.cursor.execute("SELECT * FROM `users` WHERE `telegram_id` = ?", (user_id,)).fetchone()
