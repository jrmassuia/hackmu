from interface_adapters.controller.BaseController import BaseController
from interface_adapters.pk.use_case.pk_aida_use_case import PkAidaUseCase
from interface_adapters.pk.use_case.pk_cavalada_kanturu_use_case import PkCavaladaKanturuUseCase
from interface_adapters.pk.use_case.pk_k3_use_case import PkK3UseCase
from interface_adapters.pk.use_case.pk_kanturu_use_case import PkKanturuUseCase
from interface_adapters.pk.use_case.pk_knv_use_case import PkKnvUseCase
from interface_adapters.pk.use_case.pk_tarkan_use_case import PktarkanUseCase
from utils import safe_util
from utils.rota_util import PathFinder


class PKController(BaseController):

    def _prepare(self):
        pass

    def _run(self):

        if safe_util.tk():
            self.pklizar_tarkan()
        elif safe_util.k3():
            self.pklizar_k3()
        elif safe_util.k1():
            self.pklizar_kanturus()
        else:
            self.pklizar_aida()

    def pklizar_aida(self):
        PkAidaUseCase(self.handle, PathFinder.MAPA_AIDA).execute()

    def pklizar_tarkan_knv(self):
        tarkan = PktarkanUseCase(self.handle, PathFinder.MAPA_TARKAN)
        knv = PkKnvUseCase(self.handle, PathFinder.MAPA_KANTURU_1_E_2)
        tarkan.execute()

    def pklizar_tarkan(self):
        return PktarkanUseCase(self.handle, PathFinder.MAPA_TARKAN).execute()

    def pklizar_k3(self):
        PkK3UseCase(self.handle, PathFinder.MAPA_KANTURU_3).execute()

    def pklizar_kanturus(self):
        PkKanturuUseCase(self.handle).execute()

    def cavalar_kanturu(self):
        return PkCavaladaKanturuUseCase(self.handle, PathFinder.MAPA_KANTURU_1_E_2).execute()
