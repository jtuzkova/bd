from flask import Blueprint, render_template, request
from model_route import model_route
from database.sql_provider import SQLProvider
from access import group_required
import os

query_bp = Blueprint('query_bp', __name__, template_folder='templates')

query_provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql'))

queries: dict[str, str] = {
    'bonus': 'bonus.sql',
    'passenger': 'passenger.sql',
    'no_tickets_period': 'no_tickets_period.sql',
    'passenger_bonus_range': 'passenger_bonus_range.sql',
}

@query_bp.route('/', methods=['GET'])
@group_required
def query_menu():
    return render_template('query_menu.html')


@query_bp.route('/<query_type>', methods=['GET'])
@group_required
def query_input(query_type):
    return render_template('query_input.html', query_type=query_type)


@query_bp.route('/passenger', methods=['POST'])
@group_required
def passenger_query():
    passenger_name = request.form.get('passenger_name')
    user_input = {'passenger_name': passenger_name}

    result_info = model_route(query_provider, 'passenger.sql', user_input)

    if result_info.status:
        data = result_info.result
        return render_template('query_result.html',
                               query_type='passenger',
                               products=data)
    else:
        return render_template(
            'query_input.html',
            query_type='passenger',
            error=result_info.err_message,
        )


@query_bp.route('/bonus', methods=['POST'])
@group_required
def bonus_query():
    passenger_name = request.form.get('passenger_name')
    user_input = {'passenger_name': passenger_name}

    result_info = model_route(query_provider, 'bonus.sql', user_input)

    if result_info.status:
        data = result_info.result
        return render_template('query_result.html',
                               query_type='bonus',
                               products=data)
    else:
        return render_template(
            'query_input.html',
            query_type='passenger',
            error=result_info.err_message,
        )


@query_bp.route('/no_tickets_period', methods=['POST'])
@group_required
def no_tickets_period_query():
    month = request.form.get('month')
    year = request.form.get('year')

    user_input = {
        'month': month,
        'year': year
    }

    result_info = model_route(query_provider, 'no_tickets_period.sql', user_input)

    if result_info.status:
        return render_template('query_result.html',
                               query_type='no_tickets_period',
                               products=result_info.result)
    else:
        return render_template(
            'query_input.html',
            query_type='passenger',
            error=result_info.err_message,
        )


@query_bp.route('/passenger_bonus_range', methods=['POST'])
@group_required
def passenger_bonus_range_query():
    min_bonus = request.form.get('min_bonus')
    max_bonus = request.form.get('max_bonus')

    user_input = {
        'min_bonus': min_bonus,
        'max_bonus': max_bonus
    }

    result_info = model_route(query_provider, 'passenger_bonus_range.sql', user_input)

    if result_info.status:
        return render_template('query_result.html',
                               query_type='passenger_bonus_range',
                               products=result_info.result)
    else:
        return render_template(
            'query_input.html',
            query_type='passenger',
            error=result_info.err_message,
        )