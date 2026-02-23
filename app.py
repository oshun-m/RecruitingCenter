import os
import json
from flask import Flask, render_template, session, g
from auth.blueprints.auth import bp as auth_bp
from decorators.auth import login_required
from queries.blueprints.queries import bp as queries_bp
from report.blueprint.report import bp as reports_bp
from redis import Redis
from interviews.blueprints.interviews import bp as interviews_bp
from database.sql_provider import SQLProvider
from cache.redis_cache import RedisCache


def _load_json(path, default=None):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def create_app():
    app = Flask(__name__)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    sql_dir = os.path.join(base_dir, 'sql')  # <─ только 'sql', НЕ 'queries/sql'
    if not os.path.isdir(sql_dir):
        raise RuntimeError(f'SQL dir not found: {sql_dir}')
    app.config['SQL_PROVIDER'] = SQLProvider(sql_dir)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    if not app.config['SECRET_KEY']:
        sec_path = os.path.join(data_dir, 'secret.json')
        secret_obj = _load_json(sec_path, {})
        app.config['SECRET_KEY'] = secret_obj.get('SECRET_KEY') or os.urandom(24)

    db_cfg_path = os.path.join(data_dir, 'db_config.json')
    app.config['DB_CONFIG'] = _load_json(db_cfg_path, {})
    app.config['db_config'] = app.config['DB_CONFIG']  # рабочий ключ (нижний регистр)

    access_path = os.path.join(base_dir, 'access.json')
    app.config['db_access'] = _load_json(access_path, {})

    if not os.path.isdir(sql_dir):
        raise RuntimeError(f'SQL dir not found: {sql_dir}')
    app.config['SQL_PROVIDER'] = SQLProvider(sql_dir)

    app.config['JSON_AS_ASCII'] = False
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    # REDIS
    with open('data/redis.json', 'r', encoding='utf-8') as f:
        redis_cfg = json.load(f)

    app.config['REDIS_CONFIG'] = redis_cfg
    app.config['CACHE_CONFIG'] = redis_cfg

    app.extensions['redis_cache'] = RedisCache(redis_cfg)

    with open(os.path.join(data_dir, 'access.json'), 'r', encoding='utf-8') as f:
        _access_raw = json.load(f)

    _access = {(role or '').lower(): list(map(str, sections))
               for role, sections in _access_raw.items()}

    app.config['db_access'] = _access

    print("ACCESS CFG LOADED:", app.config['db_access'])

    app.register_blueprint(auth_bp,    url_prefix='/auth')
    app.register_blueprint(queries_bp, url_prefix='/queries')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(interviews_bp, url_prefix='/interviews')



    @app.before_request
    def inject_db():
        cfg = session.get('db_config')
        if not isinstance(cfg, dict) or not cfg:
            cfg = app.config.get('db_config', {}) or app.config.get('DB_CONFIG', {})
        for k in ('host', 'user', 'password', 'database'):
            cfg.setdefault(k, app.config['DB_CONFIG'].get(k))
        app.config['db_config'] = cfg
        g.db_config = cfg

    @app.route('/')
    @login_required
    def menu():
        return render_template('menu.html', user=session.get('user'))

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5000, debug=True)
