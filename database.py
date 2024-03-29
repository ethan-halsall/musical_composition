import json
import sqlite3
from sqlite3 import Error


class Database:
    def __init__(self, path="music.db"):
        self.path = path
        table = """CREATE TABLE IF NOT EXISTS Sequence (
                                            filename TEXT PRIMARY KEY,
                                            sequences JSON,
                                            durations JSON,
                                            key TEXT
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
            conn = sqlite3.connect(self.path)
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

    def insert_or_update(self, filename, sequences, durations, key):
        data = self._fetch(
            "SELECT filename FROM Sequence WHERE filename=?", (filename,))

        if len(data) == 0:
            params = [filename, sequences, durations, key]
            try:
                insert_query = "INSERT INTO Sequence (filename, sequences, durations, key) VALUES(?,?,?,?)"
                self._insert(insert_query, params)
            except Error as e:
                print(e)
        else:
            update_params = [sequences, durations, key, filename]
            try:
                update_query = "UPDATE Sequence SET sequences = ?, durations = ?, key = ?  WHERE filename=?"
                self._insert(update_query, update_params)
            except Error as e:
                print(e)

    def get_sequence(self, filename):
        rows = self._fetch(
            "SELECT sequences FROM Sequence WHERE filename=?", (filename,))
        return rows[0][0]

    def get_durations(self, filename):
        rows = self._fetch(
            "SELECT durations FROM Sequence WHERE filename=?", (filename,))
        return rows[0][0]

    def get_key(self, filename):
        rows = self._fetch(
            "SELECT key FROM Sequence WHERE filename=?", (filename,))
        return rows[0][0]

    @staticmethod
    def to_json(lst):
        return json.dumps(lst)

    @staticmethod
    def to_lst(dump):
        return json.loads(dump)
