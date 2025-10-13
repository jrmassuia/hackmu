import socket

from interface_adapters.pk.use_case.pk_aida_use_case import PkAidaUseCase
from interface_adapters.pk.use_case.pk_tarkan_use_case import PktarkanUseCase
from utils.rota_util import PathFinder


class PKController:

    def __init__(self, handle, arduino):
        self.handle = handle
        self.arduino = arduino

    def execute(self):
        if 'PC1' in socket.gethostname():
            self.pklizar_tarkan()
        else:
            self.pklizar_aida()

    def pklizar_aida(self):
        PkAidaUseCase(self.handle, self.arduino, PathFinder.MAPA_AIDA).execute()

    def pklizar_tarkan(self):
        PktarkanUseCase(self.handle, self.arduino, PathFinder.MAPA_TARKAN).execute()
