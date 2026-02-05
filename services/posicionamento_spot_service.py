import socket
import time
from typing import Iterable, List, Optional, Sequence, Tuple

from interface_adapters.up.up_util.up_util import Up_util
from services.buscar_personagem_proximo_service_old import BuscarPersoangemProximoService
from sessao_handle import get_handle_atual
from utils import mouse_util
from utils.buscar_item_util import BuscarItemUtil
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers

# Tipos para deixar mais claro
Coord = Tuple[int, int]
GrupoSpot = Tuple[Sequence[str], Sequence[Coord], Coord]  # (classes, coords_spot, coord_mouse)


class PosicionamentoSpotService:
    def __init__(self, spots: List[List[GrupoSpot]], spot_up: Optional[int] = None):
        self.handle = get_handle_atual()

        # Recomendado: reaproveitar pointer singleton (se você já implementou)
        self.pointer = Pointers()
        # self.pointer = get_pointer()

        self.mover_spot_util = MoverSpotUtil()
        self.up_util = Up_util()
        self.buscar_personagem = BuscarPersoangemProximoService()

        self.spot_up = spot_up
        self.spots = spots

        self.classe = self.pointer.get_classe()

        self.coord_spot_atual: Optional[Coord] = None
        self.coord_mouse_atual: Optional[Coord] = None
        self.chegou_spot: bool = False

    # ============================================================
    # API pública
    # ============================================================

    def posicionar_bot_farm(self) -> bool:
        """
        Procura o primeiro spot compatível com a classe e tenta posicionar.
        """
        for classes, coordenadas_spot, coord_mouse in self._iterar_grupos():
            if self.classe not in classes:
                continue

            self.coord_spot_atual = coordenadas_spot[0]
            if self._mover_para_spot(coord_mouse, verificar_spot_livre=False):
                self._configurar_spot(coord_mouse)
                return True

        return False

    def verficar_se_char_ja_esta_spot(self) -> bool:
        """
        Se o char já estiver em um spot conhecido, configura o spot e retorna True.
        """
        y_atual = self.pointer.get_cood_y()
        x_atual = self.pointer.get_cood_x()
        if y_atual is None or x_atual is None:
            return False

        for classes, coordenadas_spot, coord_mouse in self._iterar_grupos():
            # compara com a coordenada central do spot (primeira)
            y_spot, x_spot = coordenadas_spot[0]
            if y_atual == y_spot and x_atual == x_spot:
                self.coord_spot_atual = (y_spot, x_spot)
                self._configurar_spot(coord_mouse)
                return True

        return False

    def posicionar_bot_up(self, verificar_spot_livre: bool = True) -> bool:
        """
        Posiciona o bot para UP. Pode checar se o spot está livre.
        """
        mouse_util.desativar_click_direito(self.handle)

        for classes, coordenadas_spot, coord_mouse in self._iterar_grupos():
            if self.classe not in classes:
                continue

            coord_central = coordenadas_spot[0]

            # Seu comentário diz que quando 'SM' está nas classes do spot
            # você usa a coord central para chegar mais perto
            if "SM" in classes:
                self.coord_spot_atual = coord_central
            else:
                # mesmo se não for SM, a movimentação depende do coord_spot_atual
                self.coord_spot_atual = coord_central

            if not self._mover_para_spot(coord_mouse, verificar_spot_livre=verificar_spot_livre):
                if self.mover_spot_util.esta_na_safe:
                    print("Voltou pra safe enquanto movimentava!")
                    return False
                continue

            # chegou
            if self.mover_spot_util.esta_na_safe:
                print("Voltou pra safe enquanto movimentava!")
                return False

            self.coord_spot_atual = coord_central
            self._configurar_spot(coord_mouse)
            return True

        print("Não achou spot!")
        return False

    def get_coord_spot(self):
        return self.coord_spot_atual

    def get_coord_mouse(self):
        return self.coord_mouse_atual

    def get_chegou_ao_spot(self):
        return self.chegou_spot

    # ============================================================
    # Internos
    # ============================================================

    def _iterar_grupos(self) -> Iterable[GrupoSpot]:
        """
        Itera pelos grupos aplicando o filtro de spot_up (quando informado).

        spot_up esperado: índice do spot (0-based).
        Se você usa 1-based na sua UI, ajuste aqui: spot_idx == (self.spot_up - 1)
        """
        if self.spot_up is not None:
            # mantive como 0-based (mais comum em enumerate)
            spot_idx = self.spot_up
            if 0 <= spot_idx < len(self.spots):
                for grupo in self.spots[spot_idx]:
                    yield grupo
            return

        # sem filtro: percorre todos
        for spot in self.spots:
            for grupo in spot:
                yield grupo

    def _mover_para_spot(self, coordenada_mouse: Coord, verificar_spot_livre: bool = False) -> bool:
        if not self.movimentar_mapa():
            return False

        if coordenada_mouse == (0, 0):
            return False

        if verificar_spot_livre:
            return self._spot_livre()

        return True

    def _spot_livre(self, tempo: float = 10.0) -> bool:
        """
        Verifica se o spot está livre.
        - Se hostname contém 'PC1': faz scan de chars próximos e se não tem ninguém => livre.
        - Caso contrário (ou se scan achou algo): verifica via imagem (buscar_item_spot) por até `tempo`.
        """
        hostname = socket.gethostname()

        # 1) Verificação rápida por scan (só em PC1)
        if "PC1" in hostname:
            resultados = self.buscar_personagem.listar_nomes_e_coords_por_padrao()
            if resultados:
                char_proximos = self.buscar_personagem.ordenar_proximos(resultados, limite=20)
                if len(char_proximos) == 0:
                    return True

        # 2) Verificação por imagem (instancia UMA vez)
        buscador = BuscarItemUtil()
        inicio = time.monotonic()

        while (time.monotonic() - inicio) < tempo:
            if buscador.buscar_item_spot():
                return False
            time.sleep(0.05)  # evita busy-wait

        return True

    def movimentar_mapa(self) -> bool:
        return self.mover_spot_util.movimentar(
            self.coord_spot_atual,
            verficar_se_movimentou=True,
            max_tempo=180,
            movimentacao_proxima=True,
        )

    def _configurar_spot(self, coord_mouse: Coord) -> None:
        self.coord_mouse_atual = coord_mouse
        mouse_util.mover(self.handle, *coord_mouse)
        self.up_util.ativar_up()
        self.chegou_spot = True
