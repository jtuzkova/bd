from flask import Blueprint, render_template, request, session, redirect, url_for, current_app
from model_route import model_route
from database.sql_provider import SQLProvider
from access import group_required, login_required
import os

report_bp = Blueprint('report_bp', __name__, template_folder='templates', url_prefix='/report')

report_provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql'))


@report_bp.route('/')
@login_required
def report_menu():
    user_role = session.get('user_group')
    return render_template('report_menu.html', user_role=user_role)


@report_bp.route('/<report_type>', methods=['GET'])
@group_required
def report_handle(report_type):
    rep_cfg = current_app.config.get('reports_config', {})

    if report_type not in rep_cfg:
        return render_template('message.html', msg='Неизвестный тип отчета', msg_type='error')

    return render_template('report_form.html',
                           report_type=report_type,
                           report_name=rep_cfg.get(report_type).get('name', 'Отчет'))


@report_bp.route('/<report_type>/create', methods=['POST'])
@group_required
def report_create(report_type):
    rep_cfg = current_app.config.get('reports_config', {})

    if report_type not in rep_cfg:
        return render_template('message.html', msg='Неизвестный тип отчета', msg_type='error')

    month = request.form.get('month')
    year = request.form.get('year')

    if not month or not year:
        return render_template('report_form.html',
                               report_type=report_type,
                               error='Укажите месяц и год !')

    user_input = {'month': month, 'year': year}

    result_info = model_route(report_provider, rep_cfg.get(report_type, {}).get('create_sql', ''), user_input)

    if result_info.status:
        return render_template('message.html',
                               msg=result_info.result[0].get('message'),
                               msg_type='success')
    else:
        return render_template('message.html',
                               msg=f'Ошибка при создании отчета: {result_info.err_message}',
                               msg_type='error')


@report_bp.route('/<report_type>/view', methods=['POST'])
@group_required
def report_view(report_type):
    rep_cfg = current_app.config.get('reports_config', {})

    if not report_type in rep_cfg:
        return render_template('message.html', msg='Неизвестный тип отчета', msg_type='error')

    month = request.form.get('month')
    year = request.form.get('year')

    if not month or not year:
        return render_template('report_form.html',
                               report_type=report_type,
                               error='Заполните все поля')

    user_input = {'month': month, 'year': year}

    result_info = model_route(report_provider, rep_cfg.get(report_type, {}).get('view_sql', ''), user_input)

    if result_info.status and result_info.result:
        return render_template('report_result.html',
                               reports=result_info.result,
                               report_type=report_type,
                               month=month,
                               year=year,
                               report_name=rep_cfg.get(report_type, {}).get('name', 'Отчет'),
                               column_names=rep_cfg.get(report_type, {}).get('columns', []))

    return render_template('message.html',
                           msg='Отчет за указанный период не найден',
                           msg_type='error')