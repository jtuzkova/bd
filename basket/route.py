from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app
from database.DBcm import DBContextManager
from database.sql_provider import SQLProvider
from model_route import model_route
from cache.wrapper import fetch_from_cache
from cache.redis_cache import RedisCache
import os, json

with open(os.path.join(os.path.dirname(__file__), '../data/cache_config.json'), 'r') as f:
    cache_config = json.load(f)

with open('../data/db_config.json') as f:
    db_config = json.load(f)

flight_bp = Blueprint('flight_bp', __name__, template_folder='templates')

flight_provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql'))

cache_conn = RedisCache(cache_config['redis'])


@flight_bp.route('/order', methods=['GET', 'POST'])
def show_booking_page():
    # 1. Берём параметры поиска из сессии
    params = session.get('search_params', {})
    print(params)

    # 2. Если пришёл новый поиск — обновляем параметры
    if request.method == 'POST':
        params = {
            'departure_airport': request.form.get('departure_city'),
            'arrival_airport': request.form.get('arrival_city'),
            'date': request.form.get('flight_date'),
            'class': request.form.get('ticket_class')
        }
        session['search_params'] = params
        session.modified = True
        # if new_params['departure_airport'] and new_params['arrival_airport']:
        #     params = new_params
        #     session['search_params'] = params
        #     session.modified = True

    # 3. ВСЕГДА выполняем поиск, если есть параметры (и при GET, и при POST)
    items = []
    if params:
        sql_name = "find_flights.sql"
        flights_info = model_route(flight_provider, sql_name, params)
        items = flights_info.result if flights_info.status and flights_info.result else []

    # 4. Корзина и сумма
    basket_items = session.get('basket', {})
    total_price = 0.0
    for item in basket_items.values():
        try:
            price = float(item.get('price', '0'))
        except (ValueError, TypeError):
            price = 0.0
        amount = item.get('amount', 1)
        total_price += price * amount

    return render_template(
        'basket_order_list.html',
        items=items,
        basket=basket_items,
        total_price=total_price,
        search_params=params
    )


@flight_bp.route('/add', methods=['POST'])
def add_to_basket():
    user_data = request.form
    model_add_to_basket(user_data)
    return redirect(url_for('flight_bp.show_booking_page'))

def model_add_to_basket(user_data):
    current_basket = session.get('basket', {})
    d_id = user_data.get('d_id')
    ticket_class = user_data.get('class')

    sql_name = "get_flight_by_id.sql"
    params = {'f_id': d_id, 'class': ticket_class}
    result_info = model_route(flight_provider, sql_name, params)
    print(result_info)
    if result_info.status and result_info.result:
        flight = result_info.result[0]  # первый результат

        # Формируем корзину
        basket = session.get('basket', {})
        basket_key = f"{d_id}_{ticket_class}"

        if basket_key in basket:
            basket[basket_key]['amount'] += 1
        else:
            basket[basket_key] = {
                'd_id': flight.get('d_id'),
                'f_id': flight.get('f_id'),
                'number': flight.get('number'),
                'departure_airport': flight.get('departure_airport'),
                'arrival_airport': flight.get('arrival_airport'),
                'date': flight.get('date'),
                'class': ticket_class,
                'price': flight.get('price'),
                # 'bonus_miles': flight.get('bonus_miles', 0),
                'amount': 1
            }

        session['basket'] = basket
        print('basket=', session['basket'])
    else:
        # Обработка случая, если билет не найден
        print("Билет не найден!")

    return redirect(url_for('flight_bp.show_booking_page'))


@flight_bp.route('/clear')
def clear_basket():
    session.pop('basket')
    session.pop('search_params', None)
    return redirect(url_for('flight_bp.show_booking_page'))


@flight_bp.route('/save', methods=['GET'])
def save_order():
    basket = session.get('basket', {})
    user_id = session.get('user_id')

    if not basket or not user_id:
        return redirect(url_for('flight_bp.show_booking_page'))

    order_date = date.today()

    sql_insert_order = flight_provider.get('insert_order.sql')
    sql_insert_order_list = flight_provider.get('insert_order_list.sql')

    order_id = None

    with DBContextManager(db_config) as cursor:
        if cursor is None:
            raise ValueError('Не удалось подключиться')
        else:
            cursor.execute(sql_insert_order, [user_id, order_date])
            order_id = cursor.lastrowid

            for key, item in basket.items():
                f_id = item['f_id']
                ticket_class = item['class']
                cursor.execute(sql_insert_order_list, [order_id, int(f_id), item['amount'], ticket_class])

    session.pop('basket')
    return render_template('order_saved.html', order_id=order_id)