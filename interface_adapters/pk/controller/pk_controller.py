from interface_adapters.pk.use_case.pk_aida_use_case import PkAidaUseCase
from utils.rota_util import PathFinder


class PKController:

    def __init__(self, handle, arduino):
        self.handle = handle
        self.arduino = arduino

    def execute(self):
        self.pklizar_aida()

    def pklizar_aida(self):
        PkAidaUseCase(self.handle, self.arduino, PathFinder.MAPA_AIDA).execute()

    def pklizar_tarkan(self):
        pass
