import json

from redis import Redis, DataError, ConnectionError


class RedisCache:
    def __init__(self, config: dict):
        self.config = config
        self.conn = self._connect()

    def _connect(self):
        conn = Redis(**self.config)
        return conn

    def set_value(self, name: str, value, ttl: float):
        value_js = json.dumps(value)
        try:
            self.conn.set(name=name, value=value_js)
            if ttl > 0:
                self.conn.expire(name, ttl)
            return True
        except DataError as err:
            print(err)
            return False

    def get_value(self, name):
        value_js = self.conn.get(name)
        if value_js:
            value_dict = json.loads(value_js)
            return value_dict
        return None


    def get_item_by_class(self, cache_name: str, item_id, item_class, id_field: str = 'f_id',
                          class_field: str = 'class'):
        items = self.get_value(cache_name)

        if not items:
            return None

        for item in items:
            if (str(item.get(id_field)) == str(item_id) and
                    item.get(class_field) == item_class):
                return item
        return None