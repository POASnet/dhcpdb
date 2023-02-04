import json
import re

class MACNotFound(Exception):
    pass

class MACInvalid(Exception):
    pass

class MACdb:
    def __init__(self):
        with open('oui.json', 'r') as f:
            self._db = json.load(f)

    def search(self, mac: str) -> str:
        prefix = re.sub('[^0-9A-F]', '', mac.upper())

        if len(prefix) < 6:
            raise MACInvalid

        prefix = prefix[:6]
        if prefix in self._db.keys():
            return self._db[prefix]
        else:
            raise MACNotFound



