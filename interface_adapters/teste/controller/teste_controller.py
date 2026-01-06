import win32gui

from interface_adapters.controller.BaseController import BaseController
from interface_adapters.up.up_util.up_util import Up_util
from services.buscar_personagem_proximo_service import BuscarPersonagemProximoService
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers
from utils.teclado_util import Teclado_util


class TesteController(BaseController):

    def _prepare(self):
        self.pointer = Pointers()
        self.up_util = Up_util()
        self.mover_spot = MoverSpotUtil()
        self.classe = self.pointer.get_classe()
        self.tela = win32gui.GetWindowText(self.handle)
        self.teclado_util = Teclado_util()

    def _run(self):
        busca = BuscarPersonagemProximoService()
        resultados = busca.ordenar_proximos(busca.listar_nomes_e_coords_por_padrao())
        print(resultados)

