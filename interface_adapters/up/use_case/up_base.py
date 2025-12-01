import win32gui

from interface_adapters.up.up_util.up_util import Up_util
from services.posicionamento_spot_service import PosicionamentoSpotService
from sessao_handle import get_handle_atual
from use_cases.autopick.pegar_item_use_case import PegarItemUseCase
from utils import spot_util, mouse_util
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers
from utils.rota_util import PathFinder
from utils.teclado_util import Teclado_util


class UpBase:

    def __init__(self):
        self.handle = get_handle_atual()
        self.mover_spot_util = MoverSpotUtil()
        self.tela = win32gui.GetWindowText(self.handle)
        self.up_util = Up_util()
        self.auto_pick = PegarItemUseCase(self.handle)
        self.teclado_util = Teclado_util()
        self.pointer = Pointers()
        self.classe = self.pointer.get_classe()
        #
        self.coord_spot_atual = None
        self.coord_mouse_atual = None
        self.ja_moveu_para_mapa = False
        self.up_liberado = False
        self.tempo_inicial_limpar_mob_ao_redor = 0
        self.tempo_inicial_ativar_skill = 0

    def limpar_mob_ao_redor(self):
        self.tempo_inicial_limpar_mob_ao_redor = self.up_util.limpar_mob_ao_redor(
            self.tempo_inicial_limpar_mob_ao_redor, self.classe)

    def ativar_skill(self):
        self.tempo_inicial_ativar_skill = self.up_util.ativar_skill(self.classe, self.tempo_inicial_ativar_skill)

    def corrigir_coordenada_e_mouse(self):
        if self.coord_spot_atual and self.coord_mouse_atual:
            self.mover_spot_util.movimentar(self.coord_spot_atual, verficar_se_movimentou=True)
            mouse_util.mover(self.handle, *self.coord_mouse_atual)

    def verficar_se_char_ja_esta_spot(self):
        pathfinder = PathFinder()
        spots = None

        if pathfinder.get_numero_mapa_atual() == PathFinder.MAPA_KANTURU_1_E_2:
            spots = spot_util.buscar_todos_spots_k1_k2()
        elif pathfinder.get_numero_mapa_atual() == PathFinder.MAPA_AIDA:
            spots = spot_util.buscar_todos_spots_aida()
        elif pathfinder.get_numero_mapa_atual() == PathFinder.MAPA_KALIMA:
            spots = spot_util.buscar_spots_kalima()
        elif pathfinder.get_numero_mapa_atual() == PathFinder.MAPA_TARKAN:
            spots = spot_util.buscar_todos_spots_tk()
        elif pathfinder.get_numero_mapa_atual() == PathFinder.MAPA_ICARUS:
            spots = spot_util.buscar_spots_icarus()
        elif pathfinder.get_numero_mapa_atual() == PathFinder.MAPA_KANTURU_3:
            spots = spot_util.buscar_spots_k3()

        posiconamento_service = PosicionamentoSpotService(spots)

        if posiconamento_service.verficar_se_char_ja_esta_spot():
            self.coord_mouse_atual = posiconamento_service.get_coord_mouse()
            self.coord_spot_atual = posiconamento_service.get_coord_spot()
            return True
        return False

    def executar(self):
        raise NotImplementedError()

    def posicionar_char_spot(self):
        raise NotImplementedError()

    def sair_da_safe(self):
        raise NotImplementedError()
