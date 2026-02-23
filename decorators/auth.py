from functools import wraps
from flask import session, redirect, url_for

def login_required(view):
    @wraps(view)
    def wrapped(*a, **k):
        if not session.get('user'):
            return redirect(url_for('auth.login'))
        return view(*a, **k)
    return wrapped
