import time

from interface_adapters.helpers.session_manager_new import Sessao, GenericoFields
from interface_adapters.up.up_util.up_util import Up_util
from utils import buscar_coordenada_util, mouse_util
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers
from utils.teclado_util import Teclado_util


class UpAtlansUseCase:

    def __init__(self, handle, conexao_arduino):
        self.handle = handle
        self.sessao = Sessao(handle=handle)
        self.classe = self.sessao.ler_generico(GenericoFields.CLASSE_PERSONAGEM)
        self.mover_spot_util = MoverSpotUtil(self.handle)
        self.pointer = Pointers(self.handle)
        self.up_util = Up_util(self.handle, pointer=self.pointer, conexao_arduino=conexao_arduino)
        self.teclado_util = Teclado_util(self.handle, conexao_arduino)
        self.ja_moveu_para_atlans = False
        self.tempo_inicial_limpar_mob_ao_redor = 0

    def executar(self):
        if not self.ja_moveu_para_atlans:
            self._mover_atlans()
            self.ja_moveu_para_atlans = True

        if self._esta_na_safe_atlans():
            self.ja_moveu_para_atlans = False
        else:
            self._posicionar_char_no_spot()
            self.limpar_mob_ao_redor()

    def _posicionar_char_no_spot(self):
        if self.classe == 'SM' or self.classe == 'MG':
            self._posicionar_spot_cima()
        else:
            self._posicionar_spot_baixo()

    def _posicionar_spot_cima(self):
        self.mover_spot_util.movimentar((27, 166), verficar_se_movimentou=True, movimentacao_proxima=True)
        mouse_util.moverCentro(self.handle)
        time.sleep(15)  # PARA NAO FICAR SE MOVIMENTANDO TODA HORA

    def _posicionar_spot_baixo(self):
        if self.classe == 'DL':
            self.mover_spot_util.movimentar((109, 177), verficar_se_movimentou=True)
            mouse_util.mover(self.handle, 440, 300)
        elif self.classe == 'EF':
            self.mover_spot_util.movimentar((107, 177), verficar_se_movimentou=True)
            mouse_util.mover(self.handle, 440, 300)
        elif self.classe == 'BK':
            self.mover_spot_util.movimentar((113, 176), verficar_se_movimentou=True)
            mouse_util.moverCentro(self.handle)

    def _mover_atlans(self):
        self.teclado_util.escrever_texto('/move atlans3')

    def _esta_na_safe_atlans(self):
        ycood, xcood = buscar_coordenada_util.coordernada(self.handle)
        return (xcood and ycood) and ((11 <= xcood <= 24) and (12 <= ycood <= 29))

    def limpar_mob_ao_redor(self):
        self.tempo_inicial_limpar_mob_ao_redor = self.up_util.limpar_mob_ao_redor(
            self.tempo_inicial_limpar_mob_ao_redor, self.classe)
