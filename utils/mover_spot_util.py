import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Tuple

from sessao_handle import get_handle_atual
from utils import mouse_util, safe_util
from utils.pointer_util import Pointers
from utils.rota_util import PathFinder

# ======================================================================
# Mapeamento FIXO: delta (dy,dx) na grade 9x9 (0..8) -> coordenada do mouse
# dy/dx são calculados como (dest - atual) + 4, então o centro é (4,4).
# ======================================================================

MATRIZ_POSICOES: Tuple[Tuple[Tuple[int, int], Tuple[int, int]], ...] = (((0, 0), (155, 273)),
                                                                        ((0, 1), (175, 256)),
                                                                        ((0, 2), (217, 230)),
                                                                        ((0, 3), (245, 214)),
                                                                        ((0, 4), (287, 196)),
                                                                        ((0, 5), (316, 183)),
                                                                        ((0, 6), (344, 166)),
                                                                        ((0, 7), (375, 152)),
                                                                        ((0, 8), (405, 146)),
                                                                        ((1, 0), (178, 290)),
                                                                        ((1, 1), (194, 274)),
                                                                        ((1, 2), (240, 246)),
                                                                        ((1, 3), (269, 234)),
                                                                        ((1, 4), (317, 215)),
                                                                        ((1, 5), (338, 198)),
                                                                        ((1, 6), (378, 180)),
                                                                        ((1, 7), (396, 163)),
                                                                        ((1, 8), (431, 145)),
                                                                        ((2, 0), (211, 318)),
                                                                        ((2, 1), (228, 300)),
                                                                        ((2, 2), (273, 273)),
                                                                        ((2, 3), (302, 256)),
                                                                        ((2, 4), (344, 234)),
                                                                        ((2, 5), (364, 216)),
                                                                        ((2, 6), (405, 194)),
                                                                        ((2, 7), (420, 179)),
                                                                        ((2, 8), (457, 160)),
                                                                        ((3, 0), (230, 335)),
                                                                        ((3, 1), (256, 323)),
                                                                        ((3, 2), (303, 294)),
                                                                        ((3, 3), (330, 278)),
                                                                        ((3, 4), (371, 250)),
                                                                        ((3, 5), (400, 238)),
                                                                        ((3, 6), (438, 214)),
                                                                        ((3, 7), (456, 200)),
                                                                        ((3, 8), (493, 182)),
                                                                        ((4, 0), (260, 368)),
                                                                        ((4, 1), (288, 347)),
                                                                        ((4, 2), (338, 319)),
                                                                        ((4, 3), (362, 300)),
                                                                        ((4, 4), (400, 250)),
                                                                        ((4, 5), (423, 251)),
                                                                        ((4, 6), (459, 231)),
                                                                        ((4, 7), (479, 213)),
                                                                        ((4, 8), (513, 190)),
                                                                        ((5, 0), (264, 365)),
                                                                        ((5, 1), (289, 347)),
                                                                        ((5, 2), (338, 319)),
                                                                        ((5, 3), (370, 297)),
                                                                        ((5, 4), (432, 289)),
                                                                        ((5, 5), (433, 258)),
                                                                        ((5, 6), (466, 233)),
                                                                        ((5, 7), (489, 218)),
                                                                        ((5, 8), (518, 196)),
                                                                        ((6, 0), (291, 389)),
                                                                        ((6, 1), (321, 370)),
                                                                        ((6, 2), (366, 339)),
                                                                        ((6, 3), (396, 318)),
                                                                        ((6, 4), (473, 317)),
                                                                        ((6, 5), (501, 301)),
                                                                        ((6, 6), (535, 273)),
                                                                        ((6, 7), (560, 252)),
                                                                        ((6, 8), (586, 232)),
                                                                        ((7, 0), (332, 425)),
                                                                        ((7, 1), (358, 405)),
                                                                        ((7, 2), (409, 370)),
                                                                        ((7, 3), (432, 348)),
                                                                        ((7, 4), (506, 339)),
                                                                        ((7, 5), (525, 318)),
                                                                        ((7, 6), (561, 290)),
                                                                        ((7, 7), (587, 272)),
                                                                        ((7, 8), (619, 248)),
                                                                        ((8, 0), (418, 497)),
                                                                        ((8, 1), (441, 469)),
                                                                        ((8, 2), (487, 430)),
                                                                        ((8, 3), (513, 406)),
                                                                        ((8, 4), (553, 370)),
                                                                        ((8, 5), (579, 352)),
                                                                        ((8, 6), (608, 323)),
                                                                        ((8, 7), (637, 300)),
                                                                        ((8, 8), (633, 272)))

MAPA_MOUSE_POR_DELTA: Dict[Tuple[int, int], Tuple[int, int]] = {(0, 0): (155, 273),
                                                                (0, 1): (175, 256),
                                                                (0, 2): (217, 230),
                                                                (0, 3): (245, 214),
                                                                (0, 4): (287, 196),
                                                                (0, 5): (316, 183),
                                                                (0, 6): (344, 166),
                                                                (0, 7): (375, 152),
                                                                (0, 8): (405, 146),
                                                                (1, 0): (178, 290),
                                                                (1, 1): (194, 274),
                                                                (1, 2): (240, 246),
                                                                (1, 3): (269, 234),
                                                                (1, 4): (317, 215),
                                                                (1, 5): (338, 198),
                                                                (1, 6): (378, 180),
                                                                (1, 7): (396, 163),
                                                                (1, 8): (431, 145),
                                                                (2, 0): (211, 318),
                                                                (2, 1): (228, 300),
                                                                (2, 2): (273, 273),
                                                                (2, 3): (302, 256),
                                                                (2, 4): (344, 234),
                                                                (2, 5): (364, 216),
                                                                (2, 6): (405, 194),
                                                                (2, 7): (420, 179),
                                                                (2, 8): (457, 160),
                                                                (3, 0): (230, 335),
                                                                (3, 1): (256, 323),
                                                                (3, 2): (303, 294),
                                                                (3, 3): (330, 278),
                                                                (3, 4): (371, 250),
                                                                (3, 5): (400, 238),
                                                                (3, 6): (438, 214),
                                                                (3, 7): (456, 200),
                                                                (3, 8): (493, 182),
                                                                (4, 0): (260, 368),
                                                                (4, 1): (288, 347),
                                                                (4, 2): (338, 319),
                                                                (4, 3): (362, 300),
                                                                (4, 4): (400, 250),
                                                                (4, 5): (423, 251),
                                                                (4, 6): (459, 231),
                                                                (4, 7): (479, 213),
                                                                (4, 8): (513, 190),
                                                                (5, 0): (264, 365),
                                                                (5, 1): (289, 347),
                                                                (5, 2): (338, 319),
                                                                (5, 3): (370, 297),
                                                                (5, 4): (432, 289),
                                                                (5, 5): (433, 258),
                                                                (5, 6): (466, 233),
                                                                (5, 7): (489, 218),
                                                                (5, 8): (518, 196),
                                                                (6, 0): (291, 389),
                                                                (6, 1): (321, 370),
                                                                (6, 2): (366, 339),
                                                                (6, 3): (396, 318),
                                                                (6, 4): (473, 317),
                                                                (6, 5): (501, 301),
                                                                (6, 6): (535, 273),
                                                                (6, 7): (560, 252),
                                                                (6, 8): (586, 232),
                                                                (7, 0): (332, 425),
                                                                (7, 1): (358, 405),
                                                                (7, 2): (409, 370),
                                                                (7, 3): (432, 348),
                                                                (7, 4): (506, 339),
                                                                (7, 5): (525, 318),
                                                                (7, 6): (561, 290),
                                                                (7, 7): (587, 272),
                                                                (7, 8): (619, 248),
                                                                (8, 0): (418, 497),
                                                                (8, 1): (441, 469),
                                                                (8, 2): (487, 430),
                                                                (8, 3): (513, 406),
                                                                (8, 4): (553, 370),
                                                                (8, 5): (579, 352),
                                                                (8, 6): (608, 323),
                                                                (8, 7): (637, 300),
                                                                (8, 8): (633, 272)}


@dataclass(frozen=True)
class Coordenadas:
    y: int
    x: int


class MoverSpotUtil:
    """
    Responsável por movimentar o personagem até um destino no mapa, clicando em posições na tela.

    Melhorias aplicadas:
    - matriz de posições vira constante (não recria listas a cada chamada)
    - reduz leituras repetidas de ponteiros em loops apertados
    - remove busy-wait e corrige a lógica de "chegou" (agora espera estabilizar)
    - simplifica e acelera o posicionamento do mouse quando está perto do alvo (PK)
    """

    _CENTRO_TELA_X = 400
    _CENTRO_TELA_Y = 270

    def __init__(self, handle=None):
        self.handle = handle or get_handle_atual()
        self.pointer = Pointers(hwnd=self.handle)
        self.classe = self.pointer.get_classe()
        self.esta_na_safe = False
        self.pathfinder: Optional[PathFinder] = None
        self.proxima_posicao_mouse: Optional[Tuple[int, int]] = None

    # ---------------------------
    # API pública
    # ---------------------------

    def movimentar(self, coords, **kwargs) -> bool:
        self.pathfinder = PathFinder()
        return self._movimentar_para(coords, **kwargs)

    # ---------------------------
    # Fluxo principal
    # ---------------------------

    def _movimentar_para(
            self,
            coords,
            max_tempo: float = 60,
            verficar_se_movimentou: bool = False,
            movimentacao_proxima: bool = False,
            posicionar_mouse_coordenada: bool = False,
    ) -> bool:
        return self._movimentar(
            [coords],
            max_tempo=max_tempo,
            verficar_se_movimentou=verficar_se_movimentou,
            movimentacao_proxima=movimentacao_proxima,
            posicionar_mouse_coordenada=posicionar_mouse_coordenada,
        )

    def _movimentar(
            self,
            destino,
            max_tempo: float = 60,
            verficar_se_movimentou: bool = False,
            movimentacao_proxima: bool = False,
            posicionar_mouse_coordenada: bool = False,
    ) -> bool:
        try:
            destino_y, destino_x = destino[0]
            tempo_inicio = time.time()
            x_ant, y_ant, hora_inicial = None, None, None
            self.esta_na_safe = False

            for _ in range(2):
                while True:
                    if self._tempo_excedido(tempo_inicio, max_tempo):
                        print(
                            "Tempo máximo atingido para movimentação com o char "
                            + str(self.pointer.get_nome_char())
                            + " no mapa "
                            + str(self.pathfinder.get_nome_mapa_atual())
                        )
                        return True

                    if self._verificar_se_morreu() or (
                            verficar_se_movimentou and self._checar_safe_zone(self.pathfinder.get_numero_mapa_atual())
                    ):
                        self.esta_na_safe = True
                        mouse_util.desativar_click_esquerdo(self.handle)
                        return False

                    # lê coordenadas UMA vez por iteração
                    y_atual = self.pointer.get_cood_y()
                    x_atual = self.pointer.get_cood_x()
                    if y_atual is None or x_atual is None:
                        time.sleep(0.05)
                        continue

                    if x_atual == destino_x and y_atual == destino_y:
                        return True

                    caminho = self.pathfinder.find_path((y_atual, x_atual), (destino_y, destino_x))
                    if not caminho or len(caminho) < 2:
                        time.sleep(0.03)
                        continue

                    prox_posicao = self._obter_proxima_posicao(caminho, y_atual, x_atual)
                    if not prox_posicao:
                        time.sleep(0.03)
                        continue

                    _, _, cx, cy = prox_posicao

                    executou_movimentacao_aproximada = self._executar_movimento(
                        caminho, cx, cy, movimentacao_proxima, posicionar_mouse_coordenada
                    )

                    if executou_movimentacao_aproximada:
                        return True

                    if self.pointer.get_char_pk_selecionado():  # mata mob caso esteja selecionado
                        mouse_util.clickDireito(self.handle)
                        time.sleep(1)

                    x_ant, y_ant, hora_inicial = \
                        self._verificar_e_desbloquear_coordenada_equanto_movimenta_se_necessario(
                            self.pointer.get_cood_x(),
                            self.pointer.get_cood_y(),
                            x_ant,
                            y_ant,
                            hora_inicial,
                        )

        except Exception as e:
            print(
                "Erro ao movimentar com o char "
                + str(self.pointer.get_nome_char())
                + " no mapa "
                + str(self.pathfinder.get_nome_mapa_atual())
                + f" : {e}"
            )
        return False

    # ---------------------------
    # Regras de safe / morte / tempo
    # ---------------------------

    def _checar_safe_zone(self, mapa) -> bool:
        if mapa == PathFinder.MAPA_KANTURU_1_E_2:
            return safe_util.k1()
        if mapa == PathFinder.MAPA_AIDA or mapa == PathFinder.MAPA_KALIMA:
            return safe_util.aida()
        if mapa == PathFinder.MAPA_TARKAN:
            return safe_util.tk()
        if mapa == PathFinder.MAPA_ATLANS:
            return safe_util.atlans()
        if mapa == PathFinder.MAPA_KANTURU_3:
            return safe_util.k3()
        if mapa == PathFinder.MAPA_DEVIAS:
            return safe_util.devias()
        if mapa == PathFinder.MAPA_LOSTTOWER:
            return safe_util.losttower()
        if mapa == PathFinder.MAPA_DUNGEON:
            return safe_util.lorencia()
        return False

    def _verificar_se_morreu(self) -> bool:
        return self.pointer.get_hp() == 0

    def _tempo_excedido(self, tempo_inicio, max_tempo) -> bool:
        return time.time() - tempo_inicio > max_tempo

    # ---------------------------
    # Movimento / clique / posicionamento do mouse
    # ---------------------------

    def _executar_movimento(self, caminho, cx, cy, movimentacao_proxima, posicionar_mouse_coordenada) -> bool:
        """
        Executa o clique/movimento principal.
        - Quando 'posicionar_mouse_coordenada' está ligado, tentamos posicionar o mouse
          para ficar "mirando" o próximo passo (útil no PK).
        """
        esta_proximo = len(caminho) <= 2
        clique_rapido = (not movimentacao_proxima) and len(caminho) <= 3

        if posicionar_mouse_coordenada:
            ultimas_posicoes = None

            if 2 < len(caminho) <= 8 and self.classe in ["BK", "MG"]:
                ultimas_posicoes = [caminho[-2]]
            elif 4 < len(caminho) <= 8:
                ultimas_posicoes = [caminho[-4]]

            if ultimas_posicoes:
                y_atual = self.pointer.get_cood_y()
                x_atual = self.pointer.get_cood_x()
                if y_atual is not None and x_atual is not None:
                    prox_posicao = self._obter_proxima_posicao(ultimas_posicoes, y_atual, x_atual)
                    if prox_posicao:
                        _, _, cx, cy = prox_posicao
                        mouse_util.left_clique(self.handle, cx, cy, delay=0.05)
                        esta_proximo = True

            if len(caminho) > 8:
                mouse_util.left_clique(self.handle, cx, cy, delay=0.05)
                return False

        if posicionar_mouse_coordenada and esta_proximo:
            return self._executar_movimento_e_posicionar_mouse(caminho)

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

    def _executar_movimento_e_posicionar_mouse(self, caminho) -> bool:
        """
        Versão simplificada e mais rápida do método original.

        1) Aguarda o personagem iniciar o movimento e estabilizar (sem busy-wait).
        2) Recalcula um caminho curto até o destino final (para garantir o passo correto).
        3) Move o mouse para a célula do "próximo passo" na tela, usando um mapa fixo O(1).
        """
        if not caminho or len(caminho) < 2:
            return False

        destino_y, destino_x = caminho[-1]

        pos_atual = self._aguardar_movimento_estabilizar(timeout=1.0, intervalo=0.05, estabilidade_checks=3)
        if pos_atual is None:
            return False

        novo_caminho = self.pathfinder.find_path((pos_atual.y, pos_atual.x), (destino_y, destino_x))
        if not novo_caminho or len(novo_caminho) < 2:
            return False

        proximo_y, proximo_x = novo_caminho[1]
        mouse_xy = self._mapear_mouse_para_passo(pos_atual, Coordenadas(proximo_y, proximo_x))
        if not mouse_xy:
            return False

        mx, my = mouse_xy
        self.proxima_posicao_mouse = (mx, my)
        mouse_util.mover(self.handle, mx, my)
        return True

    def _aguardar_movimento_estabilizar(
            self, timeout: float = 1.0, intervalo: float = 0.05, estabilidade_checks: int = 3
    ) -> Optional[Coordenadas]:
        """
        Espera o personagem:
        - começar a mover (detectar mudança), e depois
        - estabilizar (mesma coordenada repetida 'estabilidade_checks' vezes)

        Substitui o loop antigo (que gastava CPU e tinha lógica invertida).
        """
        y0 = self.pointer.get_cood_y()
        x0 = self.pointer.get_cood_x()
        if y0 is None or x0 is None:
            return None

        inicio = time.time()
        ultimo = (y0, x0)
        movimento_iniciado = False
        estavel = 0

        while time.time() - inicio <= timeout:
            time.sleep(intervalo)
            y = self.pointer.get_cood_y()
            x = self.pointer.get_cood_x()
            if y is None or x is None:
                continue

            atual = (y, x)

            if atual != ultimo:
                movimento_iniciado = True
                estavel = 0
                ultimo = atual
                continue

            if movimento_iniciado:
                estavel += 1
                if estavel >= estabilidade_checks:
                    return Coordenadas(y=atual[0], x=atual[1])

        return Coordenadas(y=ultimo[0], x=ultimo[1])

    def _mapear_mouse_para_passo(self, atual: Coordenadas, proximo: Coordenadas) -> Optional[Tuple[int, int]]:
        dy = (proximo.y - atual.y) + 4
        dx = (proximo.x - atual.x) + 4
        if not (0 <= dy <= 8 and 0 <= dx <= 8):
            return None
        return MAPA_MOUSE_POR_DELTA.get((dy, dx))

    # ---------------------------
    # Posicionamento (delta -> mouse)
    # ---------------------------

    def _obter_proxima_posicao(self, caminho, y_atual, x_atual):
        if len(caminho) < 2:
            return None

        y_dest, x_dest = caminho[1]

        dy = y_dest - y_atual + 4
        dx = x_dest - x_atual + 4

        if not (0 <= dy <= 8 and 0 <= dx <= 8):
            return None

        mouse_xy = MAPA_MOUSE_POR_DELTA.get((dy, dx))
        if not mouse_xy:
            return None

        cx, cy = mouse_xy
        self.proxima_posicao_mouse = (cx, cy)
        return dy, dx, cx, cy

    # Mantém compatibilidade: método existia e era chamado
    def matriz_posicoes(self):
        return list(MATRIZ_POSICOES)

    # ---------------------------
    # Limpeza de spot
    # ---------------------------

    def _verificar_e_desbloquear_coordenada_equanto_movimenta_se_necessario(self, x_atual, y_atual, x_ant, y_ant,
                                                                            hora_inicial):
        if (x_ant, y_ant) != (x_atual, y_atual):
            return x_atual, y_atual, datetime.now()
        elif hora_inicial and (datetime.now() - hora_inicial).total_seconds() >= 1.5:
            self._desbloquear_coordenada_equanto_movimenta()
            return None, None, None
        return x_ant, y_ant, hora_inicial

    def _desbloquear_coordenada_equanto_movimenta(self):
        if not self.proxima_posicao_mouse:
            return

        x, y = self.proxima_posicao_mouse

        x_centro = self._CENTRO_TELA_X
        y_centro = self._CENTRO_TELA_Y

        if y < y_centro:
            y -= 65
        elif y > y_centro:
            y += 65

        if x > x_centro:
            x += 100
        elif x < x_centro:
            x -= 100

        mouse_util.left_clique(self.handle, x, y)
