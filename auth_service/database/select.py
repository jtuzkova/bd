from database.DBcm import DBContextManager
from flask import current_app

def select_list(_sql: str, pram_list: list):
    result = []
    schema = []
    with DBContextManager(current_app.config['db_config']) as cursor:
        if cursor is None:
            raise ValueError('Не удалось подключиться')
        else:
            cursor.execute(_sql, pram_list)
            result = cursor.fetchall()
            schema = []
            for item in cursor.description:
                schema.append(item[0])
                # print(schema)
    return result, schema


def select_dict(_sql, user_input: dict):
    user_list: list = []
    for _, value in user_input.items():
        user_list.append(value)

    print('user_list', user_list)
    result, schema = select_list(_sql, user_list)
    result_dict = []
    for item in result:
        result_dict.append(dict(zip(schema, item)))
    print('result_dict', result_dict)
    return result_dict