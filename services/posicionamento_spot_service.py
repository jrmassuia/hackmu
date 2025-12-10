import socket
import time

from interface_adapters.up.up_util.up_util import Up_util
from services.buscar_personagem_proximo_service import BuscarPersoangemProximoService
from sessao_handle import get_handle_atual
from utils import mouse_util
from utils.buscar_item_util import BuscarItemUtil
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers


class PosicionamentoSpotService:
    def __init__(self, spots, spot_up=None):
        self.handle = get_handle_atual()
        self.pointer = Pointers()
        self.mover_spot_util = MoverSpotUtil()
        self.spot_up = spot_up
        self.spots = spots
        #
        self.up_util = Up_util()
        self.buscar_personagem = BuscarPersoangemProximoService()
        self.classe = self.pointer.get_classe()
        #
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
                if self.classe in classes and self._mover_para_spot(coord_mouse):
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
                    self.coord_spot_atual = coordenadas_spot[0]
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
                    conseguiu_posicionar = self._mover_para_spot(coordenada_mouse,
                                                                 verificar_spot_livre=verificar_spot_livre)
                    if self.mover_spot_util.esta_na_safe:
                        print('Voltou pra safe enquanto movimentava!')
                        return False
                    if conseguiu_posicionar:
                        self.coord_spot_atual = coordenada  # APOS ACHAR A COORDENADA ATUALIZA PARA A COORDENADA CORRETA DO CHAR
                        self._configurar_spot(coordenada_mouse)
                        return True
        print('Não achou spot!')
        return False

    def _mover_para_spot(self, coordenada_mouse, verificar_spot_livre=False):
        movimentou = self.movimentar_mapa()
        if not movimentou:
            return False
        elif coordenada_mouse == (0, 0):
            return False
        elif verificar_spot_livre:
            return self._spot_livre()
        else:
            return True

    def _spot_livre(self, tempo=10):
        if 'PC1' in socket.gethostname():
            resultados = self.buscar_personagem.listar_nomes_e_coords_por_padrao()
            if resultados:
                char_proximos = self.buscar_personagem.ordenar_proximos(resultados, limite=20)
                if len(char_proximos) == 0:
                    return True

        start_time = time.time()
        while time.time() - start_time < tempo:
            achou = BuscarItemUtil().buscar_item_spot()
            if achou:
                return False
        return True

    def movimentar_mapa(self):
        return self.mover_spot_util.movimentar(
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
