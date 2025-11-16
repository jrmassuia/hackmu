import time

from interface_adapters.up.up_util.up_util import Up_util
from services.buscar_personagem_proximo_service import BuscarPersoangemProximoService
from utils import mouse_util
from utils.buscar_item_util import BuscarItemUtil
from utils.rota_util import PathFinder


class PosicionamentoSpotService:
    def __init__(self, handle, pointer, mover_spot_util, classe, spot_up, spots, mapa, conexao_arduino=None):
        self.handle = handle
        self.pointer = pointer
        self.mover_spot_util = mover_spot_util
        self.classe = classe
        self.spot_up = spot_up
        self.spots = spots
        self.mapa = mapa
        self.up_util = Up_util(self.handle, pointer=self.pointer, conexao_arduino=conexao_arduino)
        self.buscar_personagem = BuscarPersoangemProximoService(self.pointer)

        self.coord_spot_atual = None
        self.coord_mouse_atual = None
        self.chegou_spot = False

    def posicionar_bot_farm(self):
        for spot_atual, spot in enumerate(self.spots):
            if self.spot_up is not None and 1 <= self.spot_up != spot_atual:
                continue
            for grupo in spot:
                classes, coordenadas_spot, coord_mouse = grupo
                self.coord_spot_atual = coordenadas_spot[0]
                if self.classe in classes and self._mover_para_spot():
                    self._configurar_spot(coord_mouse)
                    return True
        return False

    def verficar_se_char_ja_esta_spot(self):
        for spot_atual, spot in enumerate(self.spots):
            if self.spot_up is not None and 1 <= self.spot_up != spot_atual:
                continue
            for grupo in spot:
                classes, coordenadas_spot, coord_mouse = grupo
                if self.pointer.get_cood_y() == coordenadas_spot[0][0] and \
                        self.pointer.get_cood_x() == coordenadas_spot[0][1]:
                    self._configurar_spot(coord_mouse)
                    return True

        return False

    def posicionar_bot_up(self, verificar_spot_livre=True):
        mouse_util.desativar_click_direito(self.handle)

        for indice_spot, grupo_de_spots in enumerate(self.spots):
            for grupo in grupo_de_spots:
                classes, coordenadas_spot, coordenada_mouse = grupo
                coordenada = coordenadas_spot[0]
                if 'SM' in classes:
                    self.coord_spot_atual = coordenada  # UTILIZA PARA PEGAR A COORDENADA CENTRAL DE CADA SPOT PARA CHEGAR MAIS PROXIMO
                if self.classe in classes:
                    conseguiu_posicionar = self._mover_para_spot(verificar_spot_livre=verificar_spot_livre)
                    if self.mover_spot_util.esta_na_safe:
                        print('Voltou pra safe enquanto movimentava!')
                        return False
                    if conseguiu_posicionar:
                        self.coord_spot_atual = coordenada  # APOS ACHAR A COORDENADA ATUALIZA PARA A COORDENADA CORRETA DO CHAR
                        self._configurar_spot(coordenada_mouse)
                        return True
        print('Não achou spot!')
        return False

    def _mover_para_spot(self, verificar_spot_livre=False):
        movimentou = self.movimentar_mapa()
        if not movimentou:
            return False
        elif verificar_spot_livre:
            return self._spot_livre()
        else:
            return True

    def _spot_livre(self, tempo=10):

        # resultados = self.buscar_personagem.listar_nomes_e_coords_por_padrao()
        # if resultados:
        #     char_proximos = self.buscar_personagem.ordenar_proximos(resultados, limite=20)
        #     if len(char_proximos) == 0:
        #         return True

        start_time = time.time()
        while time.time() - start_time < tempo:
            achou = BuscarItemUtil(self.handle).buscar_item_spot()
            if achou:
                return False
        return True

    def movimentar_mapa(self):
        if self.mapa == PathFinder.MAPA_KANTURU_1_E_2:
            return self.movimentar_k1_k2()
        elif self.mapa == PathFinder.MAPA_KANTURU_3:
            return self.movimentar_K3()
        elif self.mapa == PathFinder.MAPA_AIDA:
            return self.movimentar_aida()
        elif self.mapa == PathFinder.MAPA_LAND:
            return self.movimentar_land()
        elif self.mapa == PathFinder.MAPA_TARKAN:
            return self.movimentar_tarkan()
        elif self.mapa == PathFinder.MAPA_ICARUS:
            return self.movimentar_icarus()
        elif self.mapa == PathFinder.MAPA_KALIMA:
            return self.movimentar_kalima()
        elif self.mapa == PathFinder.MAPA_NORIA:
            return self.movimentar_noria()

    def movimentar_noria(self):
        return self.mover_spot_util.movimentar_noria(
            self.coord_spot_atual,
            limpar_spot_se_necessario=True,
            verficar_se_movimentou=True,
            max_tempo=180,
            movimentacao_proxima=True
        )

    def movimentar_k1_k2(self):
        return self.mover_spot_util.movimentar_kanturu_1_2(
            self.coord_spot_atual,
            limpar_spot_se_necessario=True,
            verficar_se_movimentou=True,
            max_tempo=180,
            movimentacao_proxima=True
        )

    def movimentar_K3(self):
        return self.mover_spot_util.movimentar_kanturu_3(
            self.coord_spot_atual,
            limpar_spot_se_necessario=True,
            verficar_se_movimentou=True,
            max_tempo=180,
            movimentacao_proxima=True
        )

    def movimentar_icarus(self):
        return self.mover_spot_util.movimentar_icarus(
            self.coord_spot_atual,
            limpar_spot_se_necessario=True,
            verficar_se_movimentou=True,
            max_tempo=180,
            movimentacao_proxima=True
        )

    def movimentar_kalima(self):
        return self.mover_spot_util.movimentar_kalima(
            self.coord_spot_atual,
            limpar_spot_se_necessario=True,
            verficar_se_movimentou=True,
            max_tempo=180,
            movimentacao_proxima=True
        )

    def movimentar_aida(self):
        return self.mover_spot_util.movimentar_aida(
            self.coord_spot_atual,
            limpar_spot_se_necessario=True,
            verficar_se_movimentou=True,
            max_tempo=180,
            movimentacao_proxima=True
        )

    def movimentar_land(self):
        return self.mover_spot_util.movimentar_land(
            self.coord_spot_atual,
            limpar_spot_se_necessario=True,
            verficar_se_movimentou=True,
            max_tempo=180,
            movimentacao_proxima=True
        )

    def movimentar_tarkan(self):
        return self.mover_spot_util.movimentar_tarkan(
            self.coord_spot_atual,
            limpar_spot_se_necessario=True,
            verficar_se_movimentou=True,
            max_tempo=180,
            movimentacao_proxima=True
        )

    def _configurar_spot(self, coord_mouse):
        self.coord_mouse_atual = coord_mouse
        mouse_util.mover(self.handle, *coord_mouse)
        self.up_util.ativar_up()
        self.chegou_spot = True

    def get_coord_spot(self):
        return self.coord_spot_atual

    def get_coord_mouse(self):
        return self.coord_mouse_atual

    def get_chegou_ao_spot(self):
        return self.chegou_spot
