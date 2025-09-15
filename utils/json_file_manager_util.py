import json
import time
import msvcrt
from pathlib import Path


class JsonFileManager:
    def __init__(self, path: str, max_retries=5, retry_delay=0.1):
        self.path = Path(path)
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def _lock_file(self, file):
        msvcrt.locking(file.fileno(), msvcrt.LK_LOCK, 1)

    def _unlock_file(self, file):
        file.seek(0)
        msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)

    def read(self) -> dict:
        for _ in range(self.max_retries):
            try:
                with self.path.open("r+") as file:
                    self._lock_file(file)
                    try:
                        file.seek(0)
                        return json.load(file)
                    finally:
                        self._unlock_file(file)
            except (json.JSONDecodeError, OSError):
                time.sleep(self.retry_delay)
        raise RuntimeError("Erro ao ler JSON após várias tentativas")

    def write(self, data: dict):
        for _ in range(self.max_retries):
            try:
                with self.path.open("r+") as file:
                    self._lock_file(file)
                    try:
                        file.seek(0)
                        file.truncate()
                        json.dump(data, file, indent=4, ensure_ascii=False)
                        file.flush()
                        return
                    finally:
                        self._unlock_file(file)
            except OSError:
                time.sleep(self.retry_delay)
        raise RuntimeError("Erro ao escrever no JSON após várias tentativas")
