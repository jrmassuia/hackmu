import threading
from utils.pointer_util import Pointers

_lock = threading.Lock()
_instance = None


def get_pointer() -> Pointers:
    global _instance
    with _lock:
        if _instance is None or not getattr(_instance, "pm", None):
            _instance = Pointers()
        return _instance
