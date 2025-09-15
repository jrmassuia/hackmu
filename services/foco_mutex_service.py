import time
from contextlib import contextmanager

import win32con
import win32event


class FocoMutexService:
    MUTEX_NAME = "Global\\ControleFocoTela"
    INFINITE = 0xFFFFFFFF

    def __init__(self):
        self.mutex = None
        self.acquired = False

    def ativar_foco(self, delay_antes=0.5):
        time.sleep(delay_antes)  # Espera antes de tentar adquirir o foco (após liberação de outro)
        try:
            self.mutex = win32event.CreateMutex(None, False, self.MUTEX_NAME)
            result = win32event.WaitForSingleObject(self.mutex, self.INFINITE)
            self.acquired = result == win32con.WAIT_OBJECT_0
        except Exception as e:
            print("Erro ao tentar adquirir o mutex:", e)
            self.acquired = False

    def inativar_foco(self):
        if self.mutex and self.acquired:
            win32event.ReleaseMutex(self.mutex)
            self.acquired = False

    @contextmanager
    def focar_mutex(self):
        self.ativar_foco()
        try:
            yield
        finally:
            self.inativar_foco()
