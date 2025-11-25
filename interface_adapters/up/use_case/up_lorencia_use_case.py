import time

from interface_adapters.up.up_util.up_util import Up_util
from sessao_handle import get_handle_atual
from utils import mouse_util, safe_util
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers


class UpLorenciaUseCase:

    def __init__(self, eh_char_noob):
        self.handle = get_handle_atual()
        self.eh_char_noob = eh_char_noob
        self.pointer = Pointers()
        self.classe = self.pointer.get_classe()
        self.up_util = Up_util()
        self.tempo_inicial_ativar_skill = 0

    def executar(self):
        self._mover_lorencia()

    def _mover_lorencia(self):
        if safe_util.lorencia(self.handle):
            self._pegar_buf()
            MoverSpotUtil().movimentar((139, 221),
                                                           max_tempo=120,
                                                           limpar_spot_se_necessario=True,
                                                           verficar_se_movimentou=True,
                                                           movimentacao_proxima=True)

            if safe_util.lorencia(self.handle):
                self._mover_lorencia()
            self.up_util.ativar_up()

        self._posicionar_char_no_spot()
        self._ativar_skill()

    def _pegar_buf(self):
        if self.eh_char_noob:
            MoverSpotUtil().movimentar((170, 129), max_tempo=120)
            mouse_util.left_clique(self.handle, 539, 310)
            time.sleep(3)
            mouse_util.left_clique(self.handle, 399, 225)  # clica no ok se tiver grandinho

    def _posicionar_char_no_spot(self):
        if self.classe == 'DL':
            self._posicionar_dl()
        else:
            self._posicionar_sm()

    def _posicionar_dl(self):
        MoverSpotUtil().movimentar((143, 221))
        mouse_util.mover(self.handle, 250, 180)

    def _posicionar_sm(self):
        mouse_util.moverCentro(self.handle)

    def _ativar_skill(self):
        self.tempo_inicial_ativar_skill = self.up_util.ativar_skill(self.classe, self.tempo_inicial_ativar_skill)
