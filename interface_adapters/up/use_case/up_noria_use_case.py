import time

from interface_adapters.up.up_util.up_util import Up_util
from services.posicionamento_spot_service import PosicionamentoSpotService
from sessao_handle import get_handle_atual
from utils import mouse_util, buscar_coordenada_util, spot_util
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers


class UpNoriasUseCase:

    def __init__(self):
        self.handle = get_handle_atual()
        self.mover_spot_util = MoverSpotUtil()
        self.pointer = Pointers()
        self.up_util = Up_util()
        self.classe = self.pointer.get_classe()

        self.ja_moveu_para_noria = False
        self.tempo_inicial_limpar_mob_ao_redor = 0
        self.tempo_inicial_ativar_skill = 0
        self.coord_spot_atual = None
        self.coord_mouse_atual = None

    def executar(self):
        self._mover_noria()

    def _mover_noria(self):
        if not self.ja_moveu_para_noria:
            self._pegar_buf()
            self.ja_moveu_para_noria = True
            self._posicionar_char_spot()

        if self._esta_na_safe():
            self.ja_moveu_para_noria = False
            time.sleep(180)
        else:
            self.limpar_mob_ao_redor()
            self._ativar_skill()
            self._corrigir_coordenada_e_mouse()

    def _pegar_buf(self):
        if self.pointer.get_reset() < 30:
            while True:
                y_coord = 170
                x_coord = 119
                self.mover_spot_util.movimentar((y_coord, x_coord))
                time.sleep(1)
                if y_coord == self.pointer.get_cood_y() and x_coord == self.pointer.get_cood_x():
                    break

            mouse_util.left_clique(self.handle, 271, 172)
            time.sleep(2)
            mouse_util.left_clique(self.handle, 399, 225)  # clica no ok se tiver grandinho

    def _posicionar_char_spot(self):
        self.mover_spot_util.movimentar((208, 129), movimentacao_proxima=True)

        spots = spot_util.buscar_spots_noria()
        poscionar = PosicionamentoSpotService(spots)

        poscionar.posicionar_bot_up(verificar_spot_livre=False)

        self.coord_mouse_atual = poscionar.get_coord_mouse()
        self.coord_spot_atual = poscionar.get_coord_spot()

    def _esta_na_safe(self):
        y, x = buscar_coordenada_util.coordernada()
        return (x and y) and (90 <= x <= 130) and (165 <= y <= 201)

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
