import time

import win32gui

from interface_adapters.up.up_util.up_util import Up_util
from services.posicionamento_spot_service import PosicionamentoSpotService
from use_cases.autopick.pegar_item_use_case import PegarItemUseCase
from utils import buscar_coordenada_util, spot_util, mouse_util
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers
from utils.teclado_util import Teclado_util


class UpK3UseCase:
    def __init__(self, handle):
        self.handle = handle
        self.mover_spot_util = MoverSpotUtil()
        self.tela = win32gui.GetWindowText(self.handle)
        self.pointer = Pointers()
        self.up_util = Up_util()
        self.auto_pick = PegarItemUseCase(self.handle)
        self.teclado_util = Teclado_util()
        self.classe = self.pointer.get_classe()


        self.tempo_inicial_limpar_mob_ao_redor = 0
        self.tempo_inicial_ativar_skill = 0
        self.ja_moveu_para_k3 = False
        self.up_liberado = False
        self.coord_spot_atual = None
        self.coord_mouse_atual = None

    def executar(self):
        self._mover_k3()

    def _mover_k3(self):
        if not self.ja_moveu_para_k3:
            self.teclado_util.escrever_texto('/move kanturu3')
            time.sleep(2)
            self.ja_moveu_para_k3 = True
            self._sair_da_safe_k3()
            self._posicionar_char_spot()

        if self.up_liberado:
            if self._esta_na_safe():
                self.ja_moveu_para_k3 = False
                time.sleep(180)
            else:
                self.auto_pick.execute()
                self.limpar_mob_ao_redor()
                self._ativar_skill()
                self._corrigir_coordenada_e_mouse()

        return self.up_liberado

    def _sair_da_safe_k3(self):
        self.mover_spot_util.movimentar((94, 105), movimentacao_proxima=True)

    def _esta_na_safe(self):
        ycood, xcood = buscar_coordenada_util.coordernada(self.handle)
        return (xcood and ycood) and ((100 <= xcood <= 110) and (70 <= ycood <= 77))

    def _posicionar_char_spot(self):
        spots = spot_util.buscar_spots_k3()
        poscionar = PosicionamentoSpotService(
            self.handle,
            self.mover_spot_util,
            None,
            spots)

        achou_spot = poscionar.posicionar_bot_up()

        if achou_spot:
            self.coord_mouse_atual = poscionar.get_coord_mouse()
            self.coord_spot_atual = poscionar.get_coord_spot()
            self.up_liberado = True
        else:
            self.up_liberado = False

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
