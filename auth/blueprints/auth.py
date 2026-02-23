from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, flash
from functools import wraps
from model_route import run_sql_one, ModelRouteError
import json
from decorators.auth import login_required

bp = Blueprint('auth', __name__, template_folder='../templates')


@bp.errorhandler(ModelRouteError)
def handle_db_error(e: ModelRouteError):
    flash(str(e), 'error')
    return render_template('login.html', login=request.form.get('login', '')), 400

@login_required
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    login_ = (request.form.get('login') or '').strip()
    pass_ = (request.form.get('pass') or '').strip()

    if not login_ or not pass_:
        return render_template('login.html', error='Введите логин и пароль', login=login_)

    row = run_sql_one('autentification.sql',
                      {'login': login_, 'pass': pass_},
                      required=True, strict_one=True)

    session['user'] = {'id': row.get('in_id'), 'login': row.get('login'), 'role': row.get('role')}
    session['user_group'] = row.get('role')

    cfg = row.get('db_config')
    if isinstance(cfg, str):
        try:
            cfg = json.loads(cfg)
        except Exception:
            cfg = None
    if isinstance(cfg, dict):
        session['db_config'] = {
            'host':     cfg.get('host'),
            'user':     cfg.get('user'),
            'password': cfg.get('password'),
            'database': cfg.get('database') or current_app.config['db_config'].get('database')
        }
    else:
        session['db_config'] = current_app.config['db_config']

    return redirect(url_for('menu'))


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
