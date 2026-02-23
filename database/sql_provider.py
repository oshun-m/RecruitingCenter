import os

class SQLProvider:
    def __init__(self, root_path: str):
        self.scripts = {}

        for dirpath, dirnames, filenames in os.walk(root_path):
            for filename in filenames:
                if not filename.endswith('.sql'):
                    continue

                full_path = os.path.join(dirpath, filename)

                if filename in self.scripts:
                    # На всякий случай — чтобы не было тихих конфликтов имён
                    raise RuntimeError(f"Дублирующийся SQL-файл: {filename}")

                with open(full_path, 'r', encoding='utf-8') as f:
                    self.scripts[filename] = f.read()

    def get(self, filename: str) -> str:
        try:
            return self.scripts[filename]
        except KeyError:
            raise RuntimeError(f"SQL-скрипт {filename!r} не найден в SQLProvider")
