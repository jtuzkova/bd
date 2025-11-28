import json
from datetime import date, datetime
from redis import Redis, DataError, ConnectionError
from decimal import Decimal


class RedisCache:
    def __init__(self, config: dict):
        self.config = config
        self.conn = self._connect()

    def _connect(self):
        conn = Redis(**self.config)
        return conn

    def _json_default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} is not JSON serializable")

    def set_value(self, name: str, value, ttl: float):
        try:
            value_js = json.dumps(value, default=self._json_default, ensure_ascii=False)
            self.conn.set(name=name, value=value_js)
            if ttl > 0:
                self.conn.expire(name, ttl)
            return True
        except (DataError, TypeError) as err:
            print(f"Redis set error: {err}")
            return False

    def get_value(self, name: str):
        value_json = self.conn.get(name)
        if not value_json:
            return None
        value_dict = json.loads(value_json)
        return value_dict
