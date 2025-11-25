import time

from utils import mouse_util, acao_menu_util
from utils.buscar_item_util import BuscarItemUtil


class GuardaGemstoneService:
    def __init__(self, handle, mover_spot_util, up_util):
        self.handle = handle
        self.mover_spot_util = mover_spot_util
        self.up_util = up_util

    def guardar_gemstone_no_bau(self):
        """Guarda gemstones no baú."""

        # Movimenta para spot específico Kanturu
        self.mover_spot_util.movimentar((27, 217), max_tempo=10)
        time.sleep(1)

        # Clica no baú na coordenada especificada
        self.up_util.clicar_bau(775, 370)

        # Ajusta mouse e desativa click direito para evitar interferência
        mouse_util.mover(self.handle, 10, 10)
        time.sleep(4)

        # Busca itens na pasta específica, com precisão definida
        itens = BuscarItemUtil().buscar_varios_itens('./static/guardar_bau', precisao=0.7)

        if itens:
            for item in itens:
                x, y = item[0], item[1]
                if x > 580:
                    # Clique duplo com delay para guardar o item
                    mouse_util.right_clique(self.handle, x + 8, y + 8, delay=0.5)
                    mouse_util.right_clique(self.handle, x + 8, y + 8, delay=0.5)

        # Fecha inventário ao finalizar
        acao_menu_util.fechar_inventario(self.handle)

