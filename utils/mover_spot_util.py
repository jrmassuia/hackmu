import random
import time
from datetime import datetime

from interface_adapters.helpers.session_manager_new import *
from utils import mouse_util, safe_util
from utils.pointer_util import Pointers
from utils.rota_util import PathFinder


class MoverSpotUtil:

    def __init__(self, handle):
        self.handle = handle
        self.sessao = Sessao(handle=handle)
        self.pointer = Pointers(handle)
        self.pathfinder = None
        self.esta_na_safe = False

    def movimentar(self, coords, **kwargs):
        pathfinder = ''
        if self.pointer.get_mapa_atual() in 'Stadium':
            pathfinder = PathFinder.MAPA_STADIUM
        elif self.pointer.get_mapa_atual() in 'Lorencia':
            pathfinder = PathFinder.MAPA_LORENCIA
        elif self.pointer.get_mapa_atual() in 'Noria':
            pathfinder = PathFinder.MAPA_NORIA
        elif self.pointer.get_mapa_atual() in 'Devias':
            pathfinder = PathFinder.MAPA_DEVIAS
        elif self.pointer.get_mapa_atual() in 'Dungeon':
            pathfinder = PathFinder.MAPA_DUNGEON
        elif self.pointer.get_mapa_atual() in 'Atlans':
            pathfinder = PathFinder.MAPA_ATLANS
        elif self.pointer.get_mapa_atual() in 'LostTower':
            pathfinder = PathFinder.MAPA_LOSTTOWER
        elif self.pointer.get_mapa_atual() in 'Tarkan':
            pathfinder = PathFinder.MAPA_TARKAN
        elif self.pointer.get_mapa_atual() in 'Loren':
            pathfinder = PathFinder.MAPA_LOREN
        elif self.pointer.get_mapa_atual() in 'Aida':
            pathfinder = PathFinder.MAPA_AIDA
        elif self.pointer.get_mapa_atual() in 'Kanturu3':
            pathfinder = PathFinder.MAPA_KANTURU_3
        elif self.pointer.get_mapa_atual() in 'Kanturu' or self.pointer.get_mapa_atual() in 'Kanturu2':
            pathfinder = PathFinder.MAPA_KANTURU_1_E_2
        elif self.pointer.get_mapa_atual() in 'Land':
            pathfinder = PathFinder.MAPA_LAND
        elif self.pointer.get_mapa_atual() in 'Crywolf':
            pathfinder = ''

        return self._movimentar_para(coords, pathfinder, **kwargs)

    def _movimentar_para(self, coords, mapa,
                         max_tempo=60,
                         verficar_se_movimentou=False,
                         limpar_spot_se_necessario=False,
                         movimentacao_proxima=False,
                         posicionar_mouse_coordenada=False):
        self.pathfinder = PathFinder(mapa)
        return self._movimentar(
            [coords],
            mapa,
            max_tempo=max_tempo,
            verficar_se_movimentou=verficar_se_movimentou,
            limpar_spot_se_necessario=limpar_spot_se_necessario,
            movimentacao_proxima=movimentacao_proxima,
            posicionar_mouse_coordenada=posicionar_mouse_coordenada
        )

    # Métodos para cada mapa
    def movimentar_lorencia(self, coords, **kwargs):
        return self._movimentar_para(coords, PathFinder.MAPA_LORENCIA, **kwargs)

    def movimentar_noria(self, coords, **kwargs):
        return self._movimentar_para(coords, PathFinder.MAPA_NORIA, **kwargs)

    def movimentar_devias(self, coords, **kwargs):
        return self._movimentar_para(coords, PathFinder.MAPA_DEVIAS, **kwargs)

    def movimentar_dungeon(self, coords, **kwargs):
        return self._movimentar_para(coords, PathFinder.MAPA_DUNGEON, **kwargs)

    def movimentar_atlans(self, coords, **kwargs):
        return self._movimentar_para(coords, PathFinder.MAPA_ATLANS, **kwargs)

    def movimentar_losttower(self, coords, **kwargs):
        return self._movimentar_para(coords, PathFinder.MAPA_LOSTTOWER, **kwargs)

    def movimentar_stadium(self, coords, **kwargs):
        return self._movimentar_para(coords, PathFinder.MAPA_STADIUM, **kwargs)

    def movimentar_icarus(self, coords, **kwargs):
        return self._movimentar_para(coords, PathFinder.MAPA_ICARUS, **kwargs)

    def movimentar_kalima(self, coords, **kwargs):
        return self._movimentar_para(coords, PathFinder.MAPA_KALIMA, **kwargs)

    def movimentar_tarkan(self, coords, **kwargs):
        return self._movimentar_para(coords, PathFinder.MAPA_TARKAN, **kwargs)

    def movimentar_aida(self, coords, **kwargs):
        return self._movimentar_para(coords, PathFinder.MAPA_AIDA, **kwargs)

    def movimentar_kanturu_1_2(self, coords, **kwargs):
        return self._movimentar_para(coords, PathFinder.MAPA_KANTURU_1_E_2, **kwargs)

    def movimentar_kanturu_3(self, coords, **kwargs):
        return self._movimentar_para(coords, PathFinder.MAPA_KANTURU_3, **kwargs)

    def movimentar_loren(self, coords, **kwargs):
        return self._movimentar_para(coords, PathFinder.MAPA_LOREN, **kwargs)

    def movimentar_land(self, coords, **kwargs):
        return self._movimentar_para(coords, PathFinder.MAPA_LAND, **kwargs)

    def \
            _movimentar(self, destino, mapa,
                        max_tempo=60,
                        verficar_se_movimentou=False,
                        limpar_spot_se_necessario=False,
                        movimentacao_proxima=False,
                        posicionar_mouse_coordenada=False):
        try:

            destino_y, destino_x = destino[0]

            tempo_inicio = time.time()
            x_ant, y_ant, hora_inicial = None, None, None
            self.esta_na_safe = False

            for _ in range(2):
                while True:
                    if self._tempo_excedido(tempo_inicio, max_tempo):
                        print(
                            'Tempo máximo atingido para movimentação com o char ' + self.pointer.get_nome_char() + ' no mapa ' + mapa)
                        return True

                    if verficar_se_movimentou and self._checar_safe_zone(mapa):
                        self.esta_na_safe = True
                        mouse_util.desativar_click_esquerdo(self.handle)
                        return False

                    y_atual = self.pointer.get_cood_y()
                    x_atual = self.pointer.get_cood_x()

                    if x_atual == destino_x and y_atual == destino_y:
                        return True

                    caminho = self.pathfinder.find_path((y_atual, x_atual), (destino_y, destino_x))
                    if not caminho:
                        continue

                    prox_posicao = self._obter_proxima_posicao(caminho, y_atual, x_atual)
                    if not prox_posicao:
                        continue

                    py, px, cx, cy = prox_posicao

                    executou_movimentacao_aproximada = self._executar_movimento(caminho, cx, cy,
                                                                                movimentacao_proxima,
                                                                                posicionar_mouse_coordenada)

                    if executou_movimentacao_aproximada or (
                            self.pointer.get_cood_x() == destino_x and self.pointer.get_cood_y() == destino_y):
                        return True

                    if limpar_spot_se_necessario:
                        x_ant, y_ant, hora_inicial = self._verificar_limpeza_spot(
                            self.pointer.get_cood_x(), self.pointer.get_cood_y(), x_ant, y_ant, hora_inicial
                        )

        except Exception as e:
            print("Erro ao movimentar com o char " + self.pointer.get_nome_char() + " no mapa " + mapa + f" : {e}")

    def _checar_safe_zone(self, mapa):
        if self.pointer.get_hp() == 0:
            return True
        if mapa == PathFinder.MAPA_KANTURU_1_E_2:
            return safe_util.k1(self.handle)
        if mapa == PathFinder.MAPA_AIDA or mapa == PathFinder.MAPA_KALIMA:
            return safe_util.aida(self.handle)
        if mapa == PathFinder.MAPA_TARKAN:
            return safe_util.tk(self.handle)
        if mapa == PathFinder.MAPA_ATLANS:
            return safe_util.atlans(self.handle)
        if mapa == PathFinder.MAPA_KANTURU_3:
            return safe_util.k3(self.handle)
        if mapa == PathFinder.MAPA_DEVIAS:
            return safe_util.devias(self.handle)
        if mapa == PathFinder.MAPA_LOSTTOWER:
            return safe_util.losttower(self.handle)
        if mapa == PathFinder.MAPA_DUNGEON:
            return safe_util.lorencia(self.handle)
        return False

    def _verificar_limpeza_spot(self, x_atual, y_atual, x_ant, y_ant, hora_inicial):
        if (x_ant, y_ant) != (x_atual, y_atual):
            return x_atual, y_atual, datetime.now()
        elif hora_inicial and (datetime.now() - hora_inicial).total_seconds() >= 2:
            self._limpar_spot()
            return None, None, None
        return x_ant, y_ant, hora_inicial

    def _limpar_spot(self):
        coordenadas = [
            (392, 53),  # cima
            (144, 252),  # esquerda
            (404, 458),  # baixo
            (667, 242)  # direita
        ]

        for _ in range(random.randint(1, 4)):
            x, y = random.choice(coordenadas)
            mouse_util.left_clique(self.handle, x, y)

    def _tempo_excedido(self, tempo_inicio, max_tempo):
        return time.time() - tempo_inicio > max_tempo

    def _obter_proxima_posicao(self, caminho, y_atual, x_atual):
        y_dest, x_dest = caminho[min(len(caminho) - 1, 4)]
        dy = y_dest - y_atual + 4
        dx = x_dest - x_atual + 4

        if not (0 <= dy <= 8 and 0 <= dx <= 8):
            return None

        index = dy * 9 + dx

        try:
            (py, px), (cx, cy) = self.matriz_posicoes()[index]
            if (dy, dx) == (py, px):
                return py, px, cx, cy
        except IndexError:
            pass

        return None

    def _executar_movimento(self, caminho, cx, cy, movimentacao_proxima, posicionar_mouse_coordenada):

        esta_proximo = len(caminho) <= 4
        clique_rapido = not movimentacao_proxima and len(caminho) <= 5

        if posicionar_mouse_coordenada and esta_proximo:
            return self._executar_movimento_e_posicionar_mouse(caminho, cx, cy)

        if movimentacao_proxima and esta_proximo:
            mouse_util.left_clique(self.handle, 400, 250)
            return True

        if clique_rapido:
            mouse_util.left_clique(self.handle, cx, cy, delay=0.05)
        else:
            mouse_util.mover(self.handle, cx, cy)
            time.sleep(0.1)
            mouse_util.ativar_click_esquerdo(self.handle)

        return False

    def _executar_movimento_e_posicionar_mouse(self, caminho, cx, cy):
        mouse_util.left_clique(self.handle, cx, cy, delay=0.05)

        destino_y = caminho[len(caminho) - 1][0]
        destino_x = caminho[len(caminho) - 1][1]

        y_anterior = self.pointer.get_cood_y()
        x_anterior = self.pointer.get_cood_x()

        start_time = time.time()
        chegou = False
        while time.time() - start_time <= 1:  # REGRA PARA DAR O TEMPO DE CHEGAR NA COORDENADA APOS O CLIQUE
            if y_anterior == self.pointer.get_cood_y() and x_anterior == self.pointer.get_cood_x():
                chegou = True
                break
            else:
                y_anterior = self.pointer.get_cood_y()
                x_anterior = self.pointer.get_cood_x()
                print('PROCURANDO COORD CORRETA!')

        if chegou is False:
            return False

        y_atual = self.pointer.get_cood_y()
        x_atual = self.pointer.get_cood_x()

        try:
            caminho = self.pathfinder.find_path((y_atual, x_atual), (destino_y, destino_x))
            prox_posicao = self._obter_proxima_posicao(caminho, y_atual, x_atual)
            py, px, cx, cy = prox_posicao
            mouse_util.mover(self.handle, cx, cy)
        except:
            print('Nao achou posicionamento do mouse!')
            return False

        return True

    def matriz_posicoes(self):

        matriz0 = [[(0, 0), (155, 273)], [(0, 1), (175, 256)], [(0, 2), (217, 230)], [(0, 3), (245, 214)],
                   [(0, 4), (287, 196)], [(0, 5), (316, 183)], [(0, 6), (344, 166)], [(0, 7), (375, 152)],
                   [(0, 8), (405, 146)]]

        matriz1 = [[(1, 0), (178, 290)], [(1, 1), (194, 274)], [(1, 2), (240, 246)], [(1, 3), (269, 234)],
                   [(1, 4), (317, 215)], [(1, 5), (338, 198)], [(1, 6), (378, 180)], [(1, 7), (396, 163)],
                   [(1, 8), (431, 145)]]

        matriz2 = [[(2, 0), (211, 318)], [(2, 1), (228, 300)], [(2, 2), (273, 273)], [(2, 3), (302, 256)],
                   [(2, 4), (344, 234)], [(2, 5), (364, 216)], [(2, 6), (405, 194)], [(2, 7), (420, 179)],
                   [(2, 8), (457, 160)]]

        matriz3 = [[(3, 0), (230, 335)], [(3, 1), (256, 323)], [(3, 2), (303, 294)], [(3, 3), (330, 278)],
                   [(3, 4), (371, 250)], [(3, 5), (400, 238)], [(3, 6), (438, 214)], [(3, 7), (256, 200)],
                   [(3, 8), (493, 182)]]

        matriz4 = [[(4, 0), (260, 368)], [(4, 1), (288, 347)], [(4, 2), (338, 319)], [(4, 3), (362, 300)],
                   [(4, 4), (400, 250)], [(4, 5), (423, 251)], [(4, 6), (459, 231)], [(4, 7), (479, 213)],
                   [(4, 8), (513, 190)]]

        matriz5 = [[(5, 0), (264, 365)], [(5, 1), (289, 347)], [(5, 2), (338, 319)], [(5, 3), (370, 297)],
                   [(5, 4), (432, 289)], [(5, 5), (433, 258)], [(5, 6), (466, 233)], [(5, 7), (489, 218)],
                   [(5, 8), (518, 196)]]

        matriz6 = [[(6, 0), (291, 389)], [(6, 1), (321, 370)], [(6, 2), (366, 339)], [(6, 3), (396, 318)],
                   [(6, 4), (473, 317)], [(6, 5), (501, 301)], [(6, 6), (535, 273)], [(6, 7), (560, 252)],
                   [(6, 8), (586, 232)]]

        matriz7 = [[(7, 0), (332, 425)], [(7, 1), (358, 405)], [(7, 2), (409, 370)], [(7, 3), (432, 348)],
                   [(7, 4), (506, 339)], [(7, 5), (525, 318)], [(7, 6), (561, 290)], [(7, 7), (587, 272)],
                   [(7, 8), (619, 248)]]

        matriz8 = [[(8, 0), (418, 497)], [(8, 1), (441, 469)], [(8, 2), (487, 430)], [(8, 3), (513, 406)],
                   [(8, 4), (553, 370)], [(8, 5), (579, 352)], [(8, 6), (608, 323)], [(8, 7), (637, 300)],
                   [(8, 8), (633, 272)]]

        matriz_concatenada = sum([matriz0, matriz1, matriz2, matriz3, matriz4, matriz5, matriz6, matriz7, matriz8], [])
        return matriz_concatenada
