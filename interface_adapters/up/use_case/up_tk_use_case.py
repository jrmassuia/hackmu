import time

from interface_adapters.up.use_case.up_base import UpBase
from services.posicionamento_spot_service import PosicionamentoSpotService
from utils import spot_util, safe_util


class UpTarkanUseCase(UpBase):

    def executar(self):
        self._mover_para_tarkan()

    def _mover_para_tarkan(self):
        if not self.ja_moveu_para_mapa:
            self.teclado_util.escrever_texto('/move tarkan2')
            time.sleep(2)
            self.ja_moveu_para_mapa = True
            self.posicionar_char_spot()

        if safe_util.tk(self.handle):
            self._ir_ate_tk2()
            self.ja_moveu_para_mapa = False
        else:
            self.limpar_mob_ao_redor()
            self.ativar_skill()
            self.corrigir_coordenada_e_mouse()

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
            print("Não foi possível se mover até o local. Encerrando movimentação.")
        return movimentou

    def posicionar_char_spot(self):
        spots = spot_util.buscar_spots_tk2(nao_ignorar_spot_pk=True)
        poscionar = PosicionamentoSpotService(spots)
        poscionar.posicionar_bot_up()

        if poscionar.get_coord_mouse() is None or poscionar.get_coord_spot() is None:
            self.coord_mouse_atual, self.coord_spot_atual = self._configura_spot_caso_nao_encontre()
        else:
            self.coord_mouse_atual = poscionar.get_coord_mouse()
            self.coord_spot_atual = poscionar.get_coord_spot()

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
