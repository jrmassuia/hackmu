import socket

from interface_adapters.pk.use_case.pk_aida_use_case import PkAidaUseCase
from interface_adapters.pk.use_case.pk_cavalada_kanturu_use_case import PkCavaladaKanturuUseCase
from interface_adapters.pk.use_case.pk_k3_use_case import PkK3UseCase
from interface_adapters.pk.use_case.pk_kanturu_use_case import PkKanturuUseCase
from interface_adapters.pk.use_case.pk_knv_use_case import PkKnvUseCase
from interface_adapters.pk.use_case.pk_tarkan_use_case import PktarkanUseCase
from utils import safe_util
from utils.rota_util import PathFinder


class PKController:

    def __init__(self, handle):
        self.handle = handle

    def execute(self):

        if 'PC1' in socket.gethostname():
            if safe_util.k3(self.handle):
                self.pklizar_k3()
            elif safe_util.aida(self.handle):
                self.pklizar_aida()
            elif safe_util.k1(self.handle):
                # self.pklizar_knv()
                self.cavalar_kanturu()
            elif safe_util.tk(self.handle):
                self.pklizar_tarkan()
            else:
                self.pklizar_kanturu()

        elif 'PC2' in socket.gethostname():
            if safe_util.tk(self.handle):
                self.pklizar_tarkan()
            elif safe_util.aida(self.handle):
                self.pklizar_aida()
            elif safe_util.k3(self.handle):
                self.pklizar_k3()
            elif safe_util.k1(self.handle):
                self.pklizar_knv()
        else:
            self.pklizar_aida()

    def pklizar_aida(self):
        PkAidaUseCase(self.handle, PathFinder.MAPA_AIDA).execute()

    def pklizar_tarkan_knv(self):
        tarkan = PktarkanUseCase(self.handle, PathFinder.MAPA_TARKAN)
        knv = PkKnvUseCase(self.handle, PathFinder.MAPA_KANTURU_1_E_2)
        tarkan.execute()
        # while True:
        #     tarkan.execute(loop=False)
        #     if not tarkan.morreu:
        #         self.pklizar_knv().execute(loop=False)

    def pklizar_tarkan(self):
        return PktarkanUseCase(self.handle, PathFinder.MAPA_TARKAN).execute()

    def pklizar_knv(self):
        return PkKnvUseCase(self.handle, PathFinder.MAPA_KANTURU_1_E_2).execute()

    def pklizar_kanturu(self):
        PkKanturuUseCase(self.handle, PathFinder.MAPA_KANTURU_1_E_2).execute()

    def pklizar_k3(self):
        PkK3UseCase(self.handle, PathFinder.MAPA_KANTURU_3).execute()

    def cavalar_kanturu(self):
        return PkCavaladaKanturuUseCase(self.handle, PathFinder.MAPA_TARKAN).execute()
