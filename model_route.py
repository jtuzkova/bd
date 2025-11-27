from dataclasses import dataclass
from database.select import *
from database.sql_provider import SQLProvider


@dataclass
class ResultInfo:
    result: tuple
    status: bool
    err_message: str


def model_route(provider: SQLProvider, sql_name: str, user_input: dict):
    err_message = ''
    _sql = provider.get(sql_name)
    print('user_input', user_input)
    result = select_dict(_sql, user_input)

    print(f'{__name__ = }: {result = }')

    if result:
        return ResultInfo(result=result, status=True, err_message=err_message)
    else:
        err_message = 'Данные не найдены'
        return ResultInfo(result=result, status=False, err_message=err_message)