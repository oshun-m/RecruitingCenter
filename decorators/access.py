from functools import wraps
from flask import current_app, session, request as rq, flash, redirect, url_for


def group_required(section_name: str | None = None):
    def decorator(view):
        @wraps(view)
        def wrapped(*a, **k):
            if 'user' not in session and 'user_group' not in session:
                flash('Нужна авторизация', 'error')
                return redirect(url_for('auth.login'))

            role = session.get('user_group') or (session.get('user') or {}).get('role')

            bp_name = rq.blueprint or (rq.endpoint.split('.', 1)[0] if rq.endpoint else '')
            required = section_name or bp_name

            access = (current_app.config.get('db_access')
                      or current_app.config.get('access')
                      or {})
            allowed = set(access.get(role, []))

            if role == 'admin' or '*' in allowed or required in allowed:
                return view(*a, **k)

            current_app.logger.warning(
                "ACCESS DENIED: role=%s required=%s bp=%s allowed=%s",
                role, required, bp_name, sorted(allowed)
            )
            flash('Нет доступа к этому разделу', 'error')
            return redirect(url_for('menu'))
        return wrapped
    return decorator

