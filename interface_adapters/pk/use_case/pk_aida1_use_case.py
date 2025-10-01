from interface_adapters.helpers.session_manager_new import Sessao, GenericoFields
from interface_adapters.pk.controller.pk_controller import PKController
from interface_adapters.pk.use_case.pk_base import PkBase
from utils.mover_spot_util import MoverSpotUtil


class PkAida1UseCase():

    def __init__(self, handle, arduino):
        self.handle = handle
        self.sessao = Sessao(handle=handle)
        self.classe = self.sessao.ler_generico(GenericoFields.CLASSE_PERSONAGEM)
        self.mover_spot_util = MoverSpotUtil(self.handle)
        self.arduino = arduino

    def execute(self):
        PKController(self.handle, self.arduino, 'romualdo12').execute()
