import time

from interface_adapters.up.up_util.up_util import Up_util
from services.posicionamento_spot_service import PosicionamentoSpotService
from sessao_handle import get_handle_atual
from utils import buscar_coordenada_util, mouse_util, spot_util
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers
from utils.teclado_util import Teclado_util


class UpTarkanUseCase:
    def __init__(self):
        self.handle = get_handle_atual()
        self.mover_spot_util = MoverSpotUtil()
        self.pointer = Pointers()
        self.up_util = Up_util()
        self.teclado_util = Teclado_util()
        self.classe = self.pointer.get_classe()

        self.tempo_inicial_corrigir_coord = 0
        self.tempo_inicial_limpar_mob_ao_redor = 0
        self.tempo_inicial_ativar_skill = 0
        self.coord_spot_atual = None
        self.coord_mouse_atual = None
        self.chegou_no_spot = False
        self.ja_moveu_para_tarkan = False

    def executar(self):
        self._mover_para_tarkan()

    def _mover_para_tarkan(self):
        if not self.ja_moveu_para_tarkan:
            self.teclado_util.escrever_texto('/move tarkan2')
            time.sleep(2)
            self.ja_moveu_para_tarkan = True
            self._posicionar_char_spot()

        if self._esta_na_safe():
            self._ir_ate_tk2()
            self.ja_moveu_para_tarkan = False
        else:
            self.limpar_mob_ao_redor()
            self._ativar_skill()
            self._corrigir_coordenada_e_mouse()

    def _ir_ate_tk2(self):
        destino = (104, 137)
        tempo_maximo = 300

        movimentou = self.mover_spot_util.movimentar(
            destino,
            max_tempo=tempo_maximo,
            limpar_spot_se_necessario=True,
            verficar_se_movimentou=True,
            movimentacao_proxima=True
        )

        if not movimentou:
            self.chegou_no_spot = False
            print("Não foi possível se mover até o local. Encerrando movimentação.")
        return movimentou

    def _posicionar_char_spot(self):
        spots = spot_util.buscar_spots_tk2()
        poscionar = PosicionamentoSpotService(spots)
        poscionar.posicionar_bot_up()

        if poscionar.get_coord_mouse() is None or poscionar.get_coord_spot() is None:
            self.coord_mouse_atual, self.coord_spot_atual = self._configura_spot_caso_nao_encontre()
        else:
            self.coord_mouse_atual = poscionar.get_coord_mouse()
            self.coord_spot_atual = poscionar.get_coord_spot()

    def _configurar_para_up(self, coordenada_mouse):
        mouse_util.mover(self.handle, *coordenada_mouse)
        self.up_util.ativar_up()
        self.chegou_no_spot = True

    def _corrigir_coordenada_e_mouse(self):
        if self.coord_spot_atual and self.coord_mouse_atual:
            self.mover_spot_util.movimentar(self.coord_spot_atual, verficar_se_movimentou=True)
            mouse_util.mover(self.handle, *self.coord_mouse_atual)

    def limpar_mob_ao_redor(self):
        self.tempo_inicial_limpar_mob_ao_redor = self.up_util.limpar_mob_ao_redor(
            self.tempo_inicial_limpar_mob_ao_redor,
            self.classe)

    def _ativar_skill(self):
        self.tempo_inicial_ativar_skill = self.up_util.ativar_skill(self.classe, self.tempo_inicial_ativar_skill)

    def _esta_na_safe(self):
        y, x = buscar_coordenada_util.coordernada(self.handle)
        return (x and y) and (50 <= x <= 74) and (185 <= y <= 207)

    def _configura_spot_caso_nao_encontre(self):
        spots = [[
            [['SM', 'MG', 'BK'], [(45, 244)], (398, 240)],  # ULTIMO SPOT TK2
            [['DL', 'EF'], [(49, 242)], (307, 119)]
        ]]

        for indice_spot, grupo_de_spots in enumerate(spots):
            for grupo in grupo_de_spots:
                classes, coordenadas_spot, coordenada_mouse = grupo
                if self.classe in classes:
                    return coordenada_mouse, coordenadas_spot[0]
