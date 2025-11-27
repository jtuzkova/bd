from functools import wraps
from flask import session, redirect, url_for, current_app, request, render_template


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        else:
            return redirect(url_for('auth_bp.auth_index'))

    return wrapper


def group_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not 'user_id' in session:
            return redirect(url_for('auth_bp.auth_index'))

        access = current_app.config.get('access_config', {})
        user_request = request.path
        user_role = session.get('user_group', '')

        if not user_role in access:
            print(f'{user_role} is unknown')
            return redirect(url_for('auth_bp.auth_index'))

        if not user_request in access.get(user_role, []):
            print(f'{user_role} has no access to {user_request}')
            return render_template('access_denied.html', user_role=user_role)

        return func(*args, **kwargs)

    return wrapper