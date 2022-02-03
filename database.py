import sqlite3
from sqlite3 import Error

from PyQt5.QtCore import QRunnable, pyqtSlot
import json


class Database:
    def __init__(self, path="music.db"):
        self.path = path
        table = """CREATE TABLE IF NOT EXISTS Sequence (
                                            filename TEXT PRIMARY KEY,
                                            sequences JSON
                                        );"""

        # Create a database connection
        self.conn = self.create_connection()

        # Create database table
        if self.conn is not None:
            self.create_table(table)
        else:
            print("Error! cannot create the database connection.")

    def create_table(self, table):
        try:
            c = self.conn.cursor()
            c.execute(table)
            c.close()
        except Error as e:
            print(e)

    def create_connection(self):
        conn = None
        try:
            conn = sqlite3.connect(self.path, check_same_thread=False) #nasty hack
        except Error as e:
            print(e)

        return conn

    def _insert(self, insert_query, params):
        cur = self.conn.cursor()
        cur.execute(insert_query, params)
        self.conn.commit()
        cur.close()

    def _fetch(self, fetch_query, params=None):
        cur = self.conn.cursor()

        if params is None:
            cur.execute(fetch_query)
        else:
            cur.execute(fetch_query, params)

        rows = cur.fetchall()
        cur.close()
        return rows

    def insert(self, filename, sequences):
        data = self._fetch(
            "SELECT filename FROM Sequence WHERE filename=?", (filename,))

        if len(data) == 0:
            params = [filename, sequences]
            try:
                insert_query = "INSERT INTO Sequence (filename, sequences) VALUES(?,?)"
                self._insert(insert_query, params)
            except Error as e:
                print(e)
        else:
            update_params = [sequences, filename]
            try:
                update_query = "UPDATE Sequence SET sequences = ? WHERE filename=?"
                self._insert(update_query, update_params)
            except Error as e:
                print(e)

    def get_sequence(self, filename):
        rows = self._fetch(
            "SELECT sequences FROM Sequence WHERE filename=?", (filename,))
        return rows[0][0]

    @staticmethod
    def to_json(lst):
        return json.dumps(lst)

    @staticmethod
    def to_lst(dump):
        return json.loads(dump)


class DatabaseWorker(QRunnable, Database):
    def __init__(self):
        QRunnable.__init__(self)

    @pyqtSlot()
    def run(self):
        Database.__init__(self)

# database = Database()
# database.insert("hello", "yoyoyo")
