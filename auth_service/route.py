import json
import os

from flask import Flask, jsonify, request
from database.sql_provider import SQLProvider
from model_route import model_route

app = Flask(__name__)
app.config['SECRET_KEY'] = '1234'

with open('data/db_config.json', encoding='utf-8') as f:
    app.config['db_config'] = json.load(f)

auth_provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql'))


@app.route('/')
def find_user():
    print(f'{__name__ = }: {request.headers = }')

    auth = request.authorization  # парсинг Basic/Digest из коробки
    if not auth or not auth.username or not auth.password:
        return jsonify(error='Bad request'), 400

    user = model_route(auth_provider, 'external_user.sql', {
        'login': auth.username,
        'passwd': auth.password
    })

    if not user.result:
        return jsonify(error='User not found'), 401

    return jsonify(user=user.result[0]), 200


if __name__ == '__main__':
    app.run(
        host='localhost',
        port=5002,
        debug=True,
    )