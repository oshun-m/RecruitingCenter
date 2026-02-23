
import pymysql

class DBContextManager:
    def __init__(self, db_config: dict):
        self.db_config = db_config
        self.conn = None
        self.cur = None

    def __enter__(self):
        self.conn = pymysql.connect(
            host=self.db_config['host'],
            user=self.db_config['user'],
            password=self.db_config['password'],
            database=self.db_config['database'],
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False
        )
        self.cur = self.conn.cursor()
        return self.cur

    def __exit__(self, exc_type, exc, tb):
        try:
            if self.cur: self.cur.close()
            if self.conn:
                self.conn.rollback() if exc_type else self.conn.commit()
        finally:
            if self.conn: self.conn.close()
