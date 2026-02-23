import traceback

import pymysql
from flask import current_app
from database.select import select_list, select_one
from database.DBcm import DBContextManager

class ModelRouteError(RuntimeError):
    def __init__(self, message, *, code=None, cause=None):
        super().__init__(message)
        self.code = code
        self.cause = cause


def _load_sql_text(sql_name: str) -> str:
    provider = current_app.config.get('SQL_PROVIDER')
    if not provider:
        raise ModelRouteError("SQL-провайдер не инициализирован в приложении.")
    try:
        return provider.get(sql_name)
    except FileNotFoundError:
        raise ModelRouteError(f"SQL-файл «{sql_name}» не найден.")
    except Exception as e:
        raise ModelRouteError(f"Не удалось загрузить SQL «{sql_name}».", cause=e)


def _friendly_mysql_error(e: pymysql.MySQLError) -> ModelRouteError:
    errno = getattr(e, "errno", None) or (e.args[0] if e.args else None)
    mapping = {
        1045: "Доступ к БД запрещён (проверьте логин/пароль DB-пользователя).",
        1049: "Указанная база данных не найдена.",
        2003: "Нет соединения с сервером БД.",
        2006: "Потеряно соединение с БД.",
        1146: "Таблица/представление не существует.",
        1054: "Неизвестный столбец в SQL.",
        1064: "Синтаксическая ошибка в SQL.",
        1452: "Нарушение внешнего ключа.",
        1366: "Некорректный тип/формат данных.",
    }
    msg = mapping.get(errno, "Ошибка базы данных.")
    return ModelRouteError(f"{msg} (код {errno})", code=errno, cause=e)


def run_sql(sql_name: str, params=None):
    sql = _load_sql_text(sql_name)
    try:
        return select_list(sql, params or None)
    except pymysql.MySQLError as e:
        raise _friendly_mysql_error(e)
    except Exception as e:
        if current_app.debug:
            traceback.print_exc()
            raise ModelRouteError(f"Неизвестная ошибка: {e}", cause=e)
        raise ModelRouteError("Неизвестная ошибка при выполнении запроса.", cause=e)


def run_sql_one(sql_name: str, params=None, *, required=False, strict_one=False):
    sql = _load_sql_text(sql_name)
    try:
        if strict_one:
            # чтобы знать количество, заберём весь результат (для учебного проекта ок)
            rows = select_list(sql, params or None)
            if not rows:
                if required:
                    raise ModelRouteError("Запись не найдена по заданным параметрам.")
                return None
            if len(rows) != 1:
                raise ModelRouteError(f"Ожидалась 1 строка результата, получено: {len(rows)}. Уточните фильтры.")
            return rows[0]
        else:
            row = select_one(sql, params or None)
            if row is None and required:
                raise ModelRouteError("Запись не найдена по заданным параметрам.")
            return row
    except pymysql.MySQLError as e:
        raise _friendly_mysql_error(e)
    except ModelRouteError:
        raise
    except Exception as e:
        if current_app.debug:
            traceback.print_exc()
            raise ModelRouteError(f"Неизвестная ошибка: {e}", cause=e)
        raise ModelRouteError("Неизвестная ошибка при выполнении запроса.", cause=e)


def call_proc(proc_name: str, args: list):
    db_cfg = current_app.config['db_config']
    try:
        with DBContextManager(db_cfg) as cursor:
            cursor.callproc(proc_name, args)
            rows = cursor.fetchall()
            while cursor.nextset():
                _ = cursor.fetchall()
            return rows
    except pymysql.MySQLError as e:
        raise _friendly_mysql_error(e)
    except Exception as e:
        raise ModelRouteError("Неизвестная ошибка при выполнении запроса.", cause=e)

def exec_sql(sql_name: str, params=None) -> int:
    """INSERT/UPDATE/DELETE — возвращает rowcount."""
    from database.DBcm import DBContextManager
    import pymysql
    sql = _load_sql_text(sql_name)
    db_cfg = current_app.config['db_config']
    try:
        with DBContextManager(db_cfg) as cursor:
            cursor.execute(sql, params or None)
            return cursor.rowcount
    except pymysql.MySQLError as e:
        raise _friendly_mysql_error(e)
    except Exception as e:
        if current_app.debug:
            traceback.print_exc()
            raise ModelRouteError(f"Неизвестная ошибка: {e}", cause=e)
        raise ModelRouteError("Неизвестная ошибка при выполнении запроса.", cause=e)

def exec_insert(sql_name: str, params=None) -> int:
    """INSERT — возвращает lastrowid."""
    from database.DBcm import DBContextManager
    import pymysql
    sql = _load_sql_text(sql_name)
    db_cfg = current_app.config['db_config']
    try:
        with DBContextManager(db_cfg) as cursor:
            cursor.execute(sql, params or None)
            return cursor.lastrowid
    except pymysql.MySQLError as e:
        raise _friendly_mysql_error(e)
    except Exception as e:
        if current_app.debug:
            traceback.print_exc()
            raise ModelRouteError(f"Неизвестная ошибка: {e}", cause=e)
        raise ModelRouteError("Неизвестная ошибка при выполнении запроса.", cause=e)

