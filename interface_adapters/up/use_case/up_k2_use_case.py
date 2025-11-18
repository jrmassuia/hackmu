import time

import win32gui

from interface_adapters.helpers.session_manager_new import Sessao, GenericoFields
from interface_adapters.up.up_util.up_util import Up_util
from services.posicionamento_spot_service import PosicionamentoSpotService
from use_cases.autopick.pegar_item_use_case import PegarItemUseCase
from utils import buscar_coordenada_util, spot_util, mouse_util
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers
from utils.rota_util import PathFinder
from utils.teclado_util import Teclado_util


class UpK2UseCase:
    def __init__(self, handle, conexao_arduino):
        self.handle = handle
        self.sessao = Sessao(handle=handle)
        self.classe = self.sessao.ler_generico(GenericoFields.CLASSE_PERSONAGEM)
        self.mover_spot_util = MoverSpotUtil(self.handle)
        self.tela = win32gui.GetWindowText(self.handle)
        self.pointer = Pointers(self.handle)
        self.up_util = Up_util(self.handle, pointer=self.pointer, conexao_arduino=conexao_arduino)
        self.auto_pick = PegarItemUseCase(self.handle, conexao_arduino)
        self.teclado_util = Teclado_util(self.handle, conexao_arduino)
        #
        self.tempo_inicial_limpar_mob_ao_redor = 0
        self.tempo_inicial_ativar_skill = 0
        self.ja_moveu_para_k2 = False
        self.up_liberado = False
        self.coord_spot_atual = None
        self.coord_mouse_atual = None

    def executar(self):
        self._mover_k2()

    def _mover_k2(self):
        if not self.ja_moveu_para_k2:
            self.teclado_util.escrever_texto('/move kanturu2')
            time.sleep(2)
            self.ja_moveu_para_k2 = True
            self._posicionar_char_spot()

        if self.up_liberado:
            if self._esta_na_safe_k1():
                self.ja_moveu_para_k2 = False
                time.sleep(180)
            else:
                self.auto_pick.execute()
                self.limpar_mob_ao_redor()
                self._ativar_skill()
                self._corrigir_coordenada_e_mouse()

        return self.up_liberado

    def _esta_na_safe_k1(self):
        y, x = buscar_coordenada_util.coordernada(self.handle)
        return (x and y) and (190 <= x <= 225 and 15 <= y <= 44)

    def _posicionar_char_spot(self):
        spots = self._buscar_spots_k2()
        poscionar = PosicionamentoSpotService(
            self.handle,
            self.pointer,
            self.mover_spot_util,
            self.classe,
            None,
            spots,
            PathFinder.MAPA_KANTURU_1_E_2
        )

        achou_spot = poscionar.posicionar_bot_up()

        if achou_spot:
            self.coord_mouse_atual = poscionar.get_coord_mouse()
            self.coord_spot_atual = poscionar.get_coord_spot()
            self.up_liberado = True
        else:
            self.up_liberado = False

    def _buscar_spots_k2(self):
        spots = spot_util.buscar_todos_spots_k1_k2()
        return spots

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
