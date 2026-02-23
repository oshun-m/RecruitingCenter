
from flask import current_app
from database.DBcm import DBContextManager

def select_list(_sql: str, param_list=None) -> list:
    db_cfg = current_app.config.get('db_config')
    if not db_cfg:
        raise RuntimeError('db_config not set in app.config')
    with DBContextManager(db_cfg) as cursor:
        cursor.execute(_sql, param_list or None)
        return cursor.fetchall()

def select_one(_sql: str, param_list=None):
    rows = select_list(_sql, param_list)
    return rows[0] if rows else None


