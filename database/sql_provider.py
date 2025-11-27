import os

class SQLProvider:
    def __init__(self, file_path):
        self.scripts: dict[str, str] = {}
        for file_name in os.listdir(file_path):
            _sql = open(f'{file_path}/{file_name}').read()
            self.scripts[file_name] = _sql
    def get(self, file):
        _sql = self.scripts[file]
        return _sql