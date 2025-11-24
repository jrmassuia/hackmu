import time

from interface_adapters.up.up_util.up_util import Up_util
from services.posicionamento_spot_service import PosicionamentoSpotService
from utils import buscar_coordenada_util, mouse_util, spot_util
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers
from utils.teclado_util import Teclado_util


class UpIcarusUseCase:

    def __init__(self, handle, conexao_arduino):
        self.handle = handle
        self.mover_spot_util = MoverSpotUtil(self.handle)
        self.pointer = Pointers(self.handle)
        self.up_util = Up_util(self.handle)
        self.teclado_util = Teclado_util(self.handle)
        self.classe = self.pointer.get_classe()
        #
        self.ja_moveu_para_icarus = False
        self.tempo_inicial_limpar_mob_ao_redor = 0
        self.tempo_inicial_ativar_skill = 0
        self.coord_spot_atual = None
        self.coord_mouse_atual = None

    def executar(self):
        self._mover_icarus()

    def _mover_icarus(self):
        if not self.ja_moveu_para_icarus:
            self._pegar_buf()
            self.teclado_util.escrever_texto('/move icarus')
            time.sleep(2)
            self.ja_moveu_para_icarus = True
            self._posicionar_char_spot()

        if self._esta_na_safe_devias():
            self.ja_moveu_para_icarus = False
            time.sleep(180)
        else:
            self.limpar_mob_ao_redor()
            self._corrigir_coordenada_e_mouse()

    def _pegar_buf(self):
        if self.pointer.get_reset() < 30:
            self.teclado_util.escrever_texto('/move noria')
            time.sleep(2)
            while True:
                y_coord = 170
                x_coord = 119
                self.mover_spot_util.movimentar((y_coord, x_coord))
                if y_coord == self.pointer.get_cood_y() and x_coord == self.pointer.get_cood_x():
                    break

            mouse_util.left_clique(self.handle, 271, 172)
            time.sleep(2)
            mouse_util.left_clique(self.handle, 399, 225)  # clica no ok se tiver grandinho

    def _esta_na_safe_devias(self):
        y, x = buscar_coordenada_util.coordernada(self.handle)
        return (x and y) and (33 <= x <= 60) and (195 <= y <= 220)

    def _posicionar_char_spot(self):
        spots = spot_util.buscar_spots_icarus()
        poscionar = PosicionamentoSpotService(
            self.handle,
            self.pointer,
            self.mover_spot_util,
            None,
            spots)

        achou_spot = poscionar.posicionar_bot_up()

        self.coord_mouse_atual = poscionar.get_coord_mouse()
        self.coord_spot_atual = poscionar.get_coord_spot()

    def limpar_mob_ao_redor(self):
        self.tempo_inicial_limpar_mob_ao_redor = self.up_util.limpar_mob_ao_redor(
            self.tempo_inicial_limpar_mob_ao_redor, self.classe)

    def _ativar_skill(self):
        self.tempo_inicial_ativar_skill = self.up_util.ativar_skill(self.classe, self.tempo_inicial_ativar_skill)

    def _corrigir_coordenada_e_mouse(self):
        if self.coord_spot_atual and self.coord_mouse_atual:
            self.mover_spot_util.movimentar(self.coord_spot_atual,
                                            verficar_se_movimentou=True)
            mouse_util.mover(self.handle, *self.coord_mouse_atual)
