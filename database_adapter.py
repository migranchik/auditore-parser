import pymysql

HOST = 'localhost'
USER = 'root'
PASSWORD = 'Ilyas2006#'
DATABASE = 'get_auditorium'


class DatabaseAdapter:

    def __init__(self):
        self.connection = pymysql.connect(host=HOST, user=USER,
                                          password=PASSWORD, database=DATABASE)
        self.cursor = self.connection.cursor()

    def add_user(self, user_id, referrer_id=None):
        if referrer_id is not None:
            sql_req = "INSERT INTO `user` (`user_id`, `balance`, `ref_balance`, `parsed_chat_id`, `referrer_id`) VALUES (%s, %s, %s, %s, %s)"
            body = (user_id, 0, 0, 0, referrer_id,)
        else:
            sql_req = "INSERT INTO `user` (`user_id`, `balance`, `ref_balance`, `parsed_chat_id`) VALUES (%s, %s, %s, %s)"
            body = (user_id, 0, 0, 0,)

        self.cursor.execute(sql_req, body)
        self.connection.commit()

    def user_exists(self, user_id):
        sql_req = "SELECT * from `user` WHERE user_id = " + str(user_id)
        users = self.cursor.execute(sql_req)
        return bool(len(self.cursor.fetchall()))

    def set_balance(self, user_id, new_balance):
        sql_req = "UPDATE `user` SET `balance`=" + str(new_balance) + " WHERE user_id = " + str(user_id)
        self.cursor.execute(sql_req)

    def get_balance(self, user_id):
        sql_req = "SELECT * from `user` WHERE user_id = " + str(user_id)
        self.cursor.execute(sql_req)
        balance = self.cursor.fetchall()
        return balance[0][2]

    def add_check(self, user_id, money, bill_id):
        sql_req = "INSERT INTO `check_pay` (`user_id`, `money`, `bill_id`) VALUES (%s, %s, %s)"
        body = (user_id, money, bill_id,)
        self.cursor.execute(sql_req, body)
        self.connection.commit()

    def get_check(self, bill_id):
        sql_req = "SELECT * FROM `check_pay` WHERE bill_id = %s"
        self.cursor.execute(sql_req, str(bill_id))
        response = self.cursor.fetchall()
        if not bool(len(response)):
            return False
        return response[0]

    def delete_check(self, bill_id):
        sql_req = "DELETE FROM `check_pay` WHERE `bill_id` = %s"
        return self.cursor.execute(sql_req, str(bill_id))

    def get_referrer_id(self, user_id):
        sql_req = "SELECT * FROM `user` WHERE `user_id` = %s"
        self.cursor.execute(sql_req, user_id)
        return self.cursor.fetchall()[0][5]

    def get_ref_balance(self, user_id):
        sql_req = "SELECT * FROM `user` WHERE `user_id` = %s"
        self.cursor.execute(sql_req, user_id)
        return self.cursor.fetchall()[0][3]

    def set_ref_balance(self, user_id, new_balance):
        sql_req = "UPDATE `user` SET `ref_balance`=" + str(new_balance) + " WHERE user_id = " + str(user_id)
        self.cursor.execute(sql_req)

    def set_language(self, user_id, language_id):
        sql_req = "UPDATE `user` SET `language_id`=" + str(language_id) + " WHERE user_id = " + str(user_id)
        self.cursor.execute(sql_req)

    def get_language(self, user_id):
        sql_req = "SELECT * FROM `user` WHERE `user_id` = %s"
        self.cursor.execute(sql_req, user_id)
        return self.cursor.fetchall()[0][6]


if __name__ == "__main__":
    db = DatabaseAdapter()
    print(db.get_language(977885116))