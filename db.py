import sqlite3


class BotDataBase:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS users(user_id INT PRIMARY KEY, age INT, city TEXT, text TEXT, gender TEXT, interest TEXT);")
        self.conn.commit()

    def user_exists(self, user_id):
        result = self.cursor.execute("SELECT `id` FROM `users` WHERE `user_id` = ?", (user_id,))
        return bool(len(result.fetchall()))

    def profile_exists(self, user_id):
        result = self.cursor.execute("SELECT COUNT (*) FROM `users` WHERE `user_id` = ?", (self.get_user_id(user_id),))
        result = result.fetchone()[0]

        if result == 0:
            return False
        else:
            return True

    def get_user_id(self, user_id):
        result = self.cursor.execute("SELECT `id` FROM `users` WHERE `user_id` = ?", (user_id,))
        return result.fetchone()[0]

    def get_photo_id(self, users_id):
        result = self.cursor.execute("SELECT `user_id` FROM `users` WHERE `id` = ?", (users_id,))
        return result.fetchone()[0]

    def add_user(self, user_id):
        self.cursor.execute("INSERT INTO `users` (`user_id`) VALUES (?)", (user_id,))
        return self.conn.commit()

    def add_new_profile(self, user_id, gender, interest, name, age, city, text):
        self.cursor.execute("INSERT INTO `users` (`users_id`, `name`, `age`, `city`, `text`, `gender`, `interest`) VALUES\ (?, ?, ?, ?, ?, ?, ?)", (self.get_user_id(user_id), name, age, city.title(), text, gender, interest))
        return self.conn.commit()

    def update_text(self, user_id, new_text):
        self.cursor.execute("UPDATE `users` SET `text` = ? WHERE `user_id` = ?", (new_text, self.get_user_id(user_id)))
        return self.conn.commit()

    def get_profile_info(self, user_id):
        result = self.cursor.execute("SELECT * FROM `users` WHERE `user_id` = ?", (self.get_user_id(user_id),))
        return result.fetchall()

    def delete_profile(self, user_id):
        self.cursor.execute("DELETE FROM `users` WHERE `user_id` = ?", (self.get_user_id(user_id),))
        return self.conn.commit()

    def delete_user(self, user_id):
        self.cursor.execute("DELETE FROM `users` WHERE `id` = ?", (self.get_user_id(user_id),))
        return self.conn.commit()

    def search_profile(self, user_id, interest, city, age):
        gender: str = ""
        if interest == "ФОПФики":
            gender = "ФОПФ"
        if interest == "БМочки":
            gender = "БМочка"

        result = self.cursor.execute("SELECT * FROM `users` WHERE `user_id` != ? AND `gender` = ? AND `city` = ? AND `age` BETWEEN ? AND ?", (self.get_user_id(user_id), gender, city.title(), int(age) - 1, int(age) + 1))
        return result.fetchall()

    def close(self):
        self.conn.close()
