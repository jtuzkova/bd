from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, session
from database.DBcm import DBContextManager
from database.sql_provider import SQLProvider
from model_route import model_route
import os, json

with open(os.path.join(os.path.dirname(__file__), '../data/cache_config.json'), 'r') as f:
    cache_config = json.load(f)

with open('../data/db_config.json') as f:
    db_config = json.load(f)

flight_bp = Blueprint('flight_bp', __name__, template_folder='templates')

flight_provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql'))

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
        flight = result_info.result[0]

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
    total_tickets = sum(item.get('amount', 0) for item in basket.values())

    # Формируем список билетов в Python
    ticket_list = []
    for key, item in basket.items():
        for i in range(item.get('amount', 0)):
            ticket_list.append({
                'departure': item.get('departure_airport'),
                'arrival': item.get('arrival_airport'),
                'date': item.get('date'),
                'number': item.get('number'),
                'class': item.get('class'),
                'price': item.get('price'),
                'key': key,
                'index': len(ticket_list)  # индекс от 0
            })

    return render_template('fill_passenger.html',
                           basket=basket,
                           total_price=total_price,
                           total_tickets=total_tickets,
                           ticket_list=ticket_list)  # передаём готовый список


@flight_bp.route('/save', methods=['POST'])
def save_order():
    basket = session.get('basket', {})
    if not basket:
        return redirect(url_for('flight_bp.show_booking_page'))

    # Покупатель уже известен по pass_id в сессии
    buyer_pid = session.get('pass_id')
    if not buyer_pid:
        return "Нет пассажира в сессии"

    total_tickets = sum(item.get('amount', 0) for item in basket.values())

    # Собираем ФИО для каждого билета
    fi_list = []
    for i in range(total_tickets):
        fi = request.form.get(f'passenger_name{i}')
        if not fi:
            return "Ошибка: заполните ФИО всех пассажиров"
        fi_list.append(fi)

    order_date = date.today()
    purchase_date = date.today()

    sql_insert_order = flight_provider.get('insert_order.sql')
    sql_insert_ticket = flight_provider.get('insert_ticket.sql')
    sql_get_scale = flight_provider.get('get_scale_by_price.sql')
    sql_update_bonus = flight_provider.get('update_passenger_bonus.sql')
    sql_insert_history = flight_provider.get('insert_history.sql')
    sql_get_bonus = flight_provider.get('get_bonus_by_pid.sql')

    order_id = None
    earned_bonus_total = 0
    old_bonus = 0
    new_bonus = 0

    with DBContextManager(db_config) as cursor:
        # 1. Текущие бонусы покупателя
        cursor.execute(sql_get_bonus, [buyer_pid])
        row = cursor.fetchone()
        old_bonus = row[0] if row else 0

        # 2. Создаём заказ
        cursor.execute(sql_insert_order, [order_date])
        order_id = cursor.lastrowid

        ticket_idx = 0

        # 3. Создаём билеты и считаем мили
        for key, item in basket.items():
            d_id = item['d_id']
            ticket_class = item['class']
            price = float(item['price'])
            amount = item['amount']

            cursor.execute(sql_get_scale, [price])
            scale_result = cursor.fetchone()
            if scale_result:
                s_id = scale_result[0]
                miles = scale_result[1]
            else:
                s_id = None
                miles = 0

            for _ in range(amount):
                fi_passenger = fi_list[ticket_idx]
                ticket_idx += 1

                cursor.execute(
                    sql_insert_ticket,
                    [ticket_class, purchase_date, price,
                     buyer_pid, fi_passenger, d_id, s_id, order_id]
                )

                earned_bonus_total += miles

        # 4. Обновляем бонусы покупателя и историю
        new_bonus = old_bonus + earned_bonus_total
        cursor.execute(
            sql_update_bonus,
            [new_bonus, date.today(), buyer_pid]
        )
        cursor.execute(
            sql_insert_history,
            [old_bonus, new_bonus, date.today(), buyer_pid]
        )

    # 5. Чистим сессию и показываем результат
    session.pop('basket', None)
    session.pop('search_params', None)
    session.modified = True

    passengers_results = [{
        'old_bonus': old_bonus,
        'earned_bonus': earned_bonus_total,
        'new_bonus': new_bonus
    }]

    return render_template(
        'order_saved.html',
        order_id=order_id,
        passengers=passengers_results,
        total_tickets=total_tickets
    )