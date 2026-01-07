from interface_adapters.pk.use_case.pk_kanturu12_use_case import PkKanturu12UseCase
from interface_adapters.pk.use_case.pk_knv_use_case import PkKnvUseCase
from utils.pointer_util import Pointers
from utils.rota_util import PathFinder


class PkKanturuUseCase:

    def __init__(self, handle):
        self.pointer = Pointers()
        self.handle = handle

    def execute(self):
        char = self.pointer.get_nome_char()

        if char == 'DL_DoMall':
            self.pklizar_kanturu12()
        else:
            self.pklizar_knv()

    def pklizar_knv(self):
        PkKnvUseCase(self.handle, PathFinder.MAPA_KANTURU_1_E_2).execute()

    def pklizar_kanturu12(self):
        PkKanturu12UseCase(self.handle, PathFinder.MAPA_KANTURU_1_E_2).execute()
