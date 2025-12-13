import requests
from flask import Blueprint, render_template, request, session, redirect, url_for
from database.sql_provider import SQLProvider
from model_route import model_route
import os

auth_bp = Blueprint('auth_bp', __name__, template_folder='templates')

auth_provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql'))

queries: dict[str, str] = {
    'check_user': 'check_user.sql',
}

@auth_bp.route('/', methods=['GET', 'POST'])
def auth_index():
    if request.method == 'GET':
        return render_template('auth_form.html')

    user_type = request.form.get('user_type')
    login = request.form.get('login')
    password = request.form.get('password')

    if not login or not password:
        return render_template('auth_form.html', error='Заполните все поля')

    if user_type == 'external':
        response = requests.get(
            'http://localhost:5002/',
            auth=(login, password),
        )

        data: dict = response.json()

        if not response.ok:
            return data['error']

        user_dict = data.get('user')
        session['user_id'] = user_dict.get('u_id')
        session['pass_id'] = user_dict.get('pass_id')
        session['user_group'] = user_dict.get('role')
        session.permanent = True
        return redirect(url_for('main_menu'))

    user_data = {'login': login, 'password': password}
    result_info = model_route(auth_provider, queries['check_user'], user_data)

    if result_info.status and result_info.result:
        user = result_info.result[0]
        session['user_id'] = user.get('u_id')
        session['user_group'] = user.get('role')
        return redirect(url_for('main_menu'))

    return render_template('auth_form.html', error='Ошибка авторизации')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth_bp.auth_index'))
