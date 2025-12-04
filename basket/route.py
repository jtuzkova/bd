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

# cache_conn = RedisCache(cache_config['redis'])
#
# @fetch_from_cache("find_flights", cache_config)
# def cached_find_flights(params):
#     sql_name = "find_flights.sql"
#     flights_info = model_route(flight_provider, sql_name, params)
#     return flights_info.result if flights_info.status and flights_info.result else []
#

@flight_bp.route('/order', methods=['GET', 'POST'])
def show_booking_page():
    params = session.get('search_params', {})
    print(params)

    if request.method == 'POST':
        params = {
            'arrival_airport': request.form.get('arrival_city'),
            'class': request.form.get('ticket_class'),
            'date': request.form.get('flight_date'),
            'departure_airport': request.form.get('departure_city'),
        }
        session['search_params'] = params
        session.modified = True
    elif not params:
        return render_template('booking_page.html',
                               items=[], basket=session.get('basket'), total_price=0.0,
                               search_params={})

    sql_name = "find_flights.sql"
    flights_info = model_route(flight_provider, sql_name, params)
    items = flights_info.result if flights_info.status and flights_info.result else []

    basket_items = session.get('basket', {})
    total_price = 0.0

    for item in basket_items.values():
        try:
            price = float(item.get('price', '0'))
        except (ValueError, TypeError):
            price = 0.0
        amount = item.get('amount', 1)
        total_price += price * amount

    session['total_price'] = total_price
    session.modified = True

    return render_template(
        'booking_page.html',
        items=items,
        basket=basket_items,
        total_price=total_price,
        search_params=params,
    )


@flight_bp.route('/add', methods=['POST'])
def add_to_basket():
    user_data = request.form
    print("user_data", user_data)
    model_add_to_basket(user_data)
    return redirect(url_for('flight_bp.show_booking_page'))

def model_add_to_basket(user_data):
    d_id = user_data.get('d_id')
    ticket_class = user_data.get('class')

    sql_name = "get_flight_by_id.sql"
    params = {'f_id': d_id, 'class': ticket_class}
    result_info = model_route(flight_provider, sql_name, params)

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
                'amount': 1
            }

        session['basket'] = basket
        print('basket=', session['basket'])

    return redirect(url_for('flight_bp.show_booking_page'))


@flight_bp.route('/clear')
def clear_basket():
    session.pop('basket')
    return redirect(url_for('flight_bp.show_booking_page'))


@flight_bp.route('/fill', methods=['GET'])
def fill_passenger():
    basket = session.get('basket', {})
    if not basket:
        return redirect(url_for('flight_bp.show_booking_page'))

    total_price = session.get('total_price', 0.0)
    return render_template('fill_passenger.html', basket=basket, total_price=total_price)


@flight_bp.route('/save', methods=['POST'])
def save_order():
    basket = session.get('basket', {})

    passenger_name = request.form.get('passenger_name')
    passenger_birthday = request.form.get('birthday')

    print('=== SAVE ORDER START ===')
    print('PASSENGER:', passenger_name, passenger_birthday)
    print('BASKET:', basket)

    if not basket:
        print('NO BASKET')
        return redirect(url_for('flight_bp.show_booking_page'))

    order_date = date.today()
    purchase_date = date.today()

    sql_insert_order = flight_provider.get('insert_order.sql')
    sql_insert_passenger = flight_provider.get('insert_passenger.sql')
    sql_get_passenger = flight_provider.get('get_passenger.sql')
    sql_insert_ticket = flight_provider.get('insert_ticket.sql')
    sql_get_scale = flight_provider.get('get_scale_by_price.sql')
    sql_update_bonus = flight_provider.get('update_passenger_bonus.sql')
    sql_insert_history = flight_provider.get('insert_history.sql')

    order_id = None
    total_bonus_miles = 0
    new_bonus_miles = 0

    with DBContextManager(db_config) as cursor:
        if cursor is None:
            raise ValueError('Не удалось подключиться')

        # 1. Заказ
        print('1) INSERT ORDER:', order_date)
        cursor.execute(sql_insert_order, [order_date])
        order_id = cursor.lastrowid
        print('   NEW ORDER_ID:', order_id)

        # 2. Пассажир
        print('2) GET PASSENGER')
        cursor.execute(sql_get_passenger, [passenger_name, passenger_birthday])
        passenger_result = cursor.fetchone()
        print('   PASSENGER_RESULT:', passenger_result)

        if passenger_result:
            p_id = passenger_result[0]
            old_bonus_miles = passenger_result[1]
            print('   EXISTING PASSENGER p_id=', p_id,
                  'old_bonus_miles=', old_bonus_miles)
        else:
            print('   CREATE NEW PASSENGER')
            cursor.execute(
                sql_insert_passenger,
                [passenger_name, passenger_birthday, 0, date.today()]
            )
            p_id = cursor.lastrowid
            old_bonus_miles = 0
            print('   NEW p_id=', p_id)

        total_bonus_miles = 0

        # 3. Билеты
        print('3) PROCESS TICKETS')
        for key, item in basket.items():
            print('   ITEM:', key, item)
            d_id = item['d_id']
            ticket_class = item['class']
            amount = item['amount']
            price = float(item['price'])
            print(f'   d_id={d_id}, class={ticket_class}, '
                  f'amount={amount}, price={price}')

            for i in range(amount):
                print(f'     TICKET #{i+1} FOR ITEM {key}')
                cursor.execute(sql_get_scale, [price])
                scale_result = cursor.fetchone()
                print('       SCALE_RESULT:', scale_result)

                if scale_result:
                    s_id = scale_result[0]
                    miles = scale_result[1]
                else:
                    s_id = None
                    miles = 0
                print('       s_id=', s_id, 'miles=', miles)

                total_bonus_miles += miles
                print('       total_bonus_miles NOW =', total_bonus_miles)

                cursor.execute(
                    sql_insert_ticket,
                    [ticket_class, purchase_date, price, p_id, d_id, s_id, order_id]
                )
                print('       TICKET INSERTED, lastrowid=', cursor.lastrowid)

        # 4. Обновление бонусов
        new_bonus_miles = old_bonus_miles + total_bonus_miles
        print('4) UPDATE BONUS:',
              'old=', old_bonus_miles,
              'earned=', total_bonus_miles,
              'new=', new_bonus_miles)

        cursor.execute(sql_update_bonus, [new_bonus_miles, date.today(), p_id])

        # 5. История
        print('5) INSERT HISTORY:',
              'old=', old_bonus_miles,
              'new=', new_bonus_miles)
        cursor.execute(sql_insert_history,
                       [old_bonus_miles, new_bonus_miles, date.today(), p_id])

    session.pop('basket', None)
    session.pop('search_params', None)
    session.modified = True
    print('=== SAVE ORDER END ===')

    return render_template(
        'order_saved.html',
        order_id=order_id,
        earned_bonus=total_bonus_miles,
        new_bonus=new_bonus_miles
    )

