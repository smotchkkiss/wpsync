import json
import os


class PersistentDict(dict):
    """
    A dict that persists its data in a JSON file
    old data is only loaded upon creation, no auto reloads on item
    lookup atm (single thread mode)
    """

    def __init__(self, persistence_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._persistence_path = os.path.abspath(persistence_path)
        try:
            self.load()
        except FileNotFoundError:
            pass

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.save()

    def __delitem__(self, key):
        super().__delitem__(key)
        self.save()

    def load(self):
        with open(self._persistence_path, "r", encoding="utf8") as f:
            data = json.load(f)
            for key in data:
                super().__setitem__(key, data[key])

    def save(self):
        dirname = os.path.dirname(self._persistence_path)
        os.makedirs(dirname, 0o755, exist_ok=True)
        with open(self._persistence_path, "w", encoding="utf8") as f:
            json.dump(self, f)
