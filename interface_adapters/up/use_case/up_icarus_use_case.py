import time

from interface_adapters.up.use_case.up_base import UpBase
from services.posicionamento_spot_service import PosicionamentoSpotService
from utils import mouse_util, spot_util, safe_util


class UpIcarusUseCase(UpBase):

    def executar(self):
        self._mover_icarus()

    def _mover_icarus(self):
        if not self.ja_moveu_para_mapa:
            self._pegar_buf()
            self.teclado_util.escrever_texto('/move icarus')
            time.sleep(2)
            self.ja_moveu_para_mapa = True
            self.posicionar_char_spot()

        if safe_util.devias(self.pointer.get_coordernada_y_x()):
            self.ja_moveu_para_mapa = False
            time.sleep(180)
        else:
            self.limpar_mob_ao_redor()
            self.corrigir_coordenada_e_mouse()

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

    def posicionar_char_spot(self):
        spots = spot_util.buscar_spots_icarus()
        poscionar = PosicionamentoSpotService(spots)

        achou_spot = poscionar.posicionar_bot_up()

        self.coord_mouse_atual = poscionar.get_coord_mouse()
        self.coord_spot_atual = poscionar.get_coord_spot()
