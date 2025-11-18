import random
import time

from utils import mouse_util, buscar_item_util, screenshot_util, acao_menu_util
from utils.buscar_item_util import BuscarItemUtil
from utils.teclado_util import Teclado_util


class RefinarGemstoneController:

    def __init__(self, handle, conexao_arduino):
        self.handle = handle
        self.conexao_arduino = conexao_arduino
        self.teclado_util = Teclado_util(self.handle, conexao_arduino)
        self.tempo = .5
        self.pos_y_ultima_joh = 0
        self.pos_x_ultima_joh = 0
        self.qtd_falha = 0
        self.execute()

    def execute(self):
        self._iniciar_processo()

    def _iniciar_processo(self):
        # MoverSpotUtil(self.handle).movimentar((75, 177))
        self.refinar()

    def refinar(self):
        """Combina itens enquanto houver itens para combinar."""
        while True:
            if not self._preparar_combinar():
                acao_menu_util.pressionar_painel_inventario(self.handle, self.conexao_arduino)
                # self.teclado_util.escrever_texto('/move noria')
                exit()

    def _preparar_combinar(self):
        """Prepara o processo de combinação de itens."""
        self._clicar_na_elpis()
        time.sleep(.25)
        self._clicar_na_opcao_refinar_gemstone()
        time.sleep(.25)
        return self._mover_gemstone_para_cm()

    def _clicar_na_elpis(self):
        self._mover_click(450, 250) # 75, 177
        # self._mover_click(480, 240)  # 75 176
        # self._mover_click(490, 200)  # 77 174

    def _clicar_na_opcao_refinar_gemstone(self):
        self._mover_click(450, 350)

    def _mover_gemstone_para_cm(self):
        """Move o item gemstone para a área de combinação."""
        image_position = BuscarItemUtil(self.handle).buscar_item_simples('./static/inventario/gemstone.png')
        if image_position:
            cpX, cpY = image_position
            self._mover_click(cpX, cpY)  # Clica no 'gemstone'
            x, y = self._campo_na_cm_para_mover_cp()
            if x is not None and y is not None:
                self._mover_click(x, y)  # Move para CM
                self._clicar_na_opcao_processar_refinamento()
                self._mover_joh_para_invenario()
                # time.sleep(self.tempo)
            return True
        return False

    def _campo_na_cm_para_mover_cp(self):
        """Seleciona um campo aleatório na área de combinação."""

        if self.pos_x_ultima_joh > 0 or self.pos_y_ultima_joh > 0:
            return self.pos_x_ultima_joh, self.pos_y_ultima_joh

        n = random.randint(1, 32)
        count = 0
        screenshot_cm = screenshot_util.capture_window(self.handle)
        image_positions = buscar_item_util.buscar_posicoes_item_epecifico(
            './static/inventario/campovazio.png', screenshot_cm, confidence_=0.85)

        if image_positions:
            for image in image_positions:
                count += 1
                if count == n:
                    return image[0], image[1]
        return None, None

    def _clicar_na_opcao_processar_refinamento(self):
        """Clica nas opções para processar a combinação."""
        self._mover_click(430, 490)  # Clica no 'refinar'
        time.sleep(.25)
        self._mover_click(310, 260)  # Clica no 'ok'
        time.sleep(.25)

    def _mover_joh_para_invenario(self):
        conta = 0.0
        self.pos_y_ultima_joh = 0
        self.pos_x_ultima_joh = 0
        self.qtd_falha = self.qtd_falha + 1
        while conta <= 2:
            time.sleep(.2)
            screenshot_cm = screenshot_util.capture_window(self.handle)
            image_positions = buscar_item_util.buscar_posicoes_item_epecifico(
                './static/inventario/joh.png', screenshot_cm, confidence_=0.9)

            if image_positions:
                x, y = image_positions[0]
                if x < 590:
                    self._mover_click(x, y)  # Clica na joh
                    self._mover_para_inventario(screenshot_cm)
                    self.pos_x_ultima_joh = x
                    self.qtd_falha = 0
                    if y <= 160:
                        self.pos_y_ultima_joh = y + 65
                    else:
                        self.pos_y_ultima_joh = y - 20
                    break

            conta += 0.1

        acao_menu_util.pressionar_painel_inventario(self.handle, self.conexao_arduino)

    def _mover_para_inventario(self, screenshot_cm):
        image_positions = buscar_item_util.buscar_posicoes_item_epecifico(
            './static/inventario/campovazioinventario.png', screenshot_cm)

        if image_positions:
            for image in image_positions:
                x, y = image
                if x >= 590:  # Achou campo no inventário
                    self._mover_click(x, y)  # Move joh para inventário
                    break

    def _mover_click(self, x, y, delay=0.1):
        """Move o mouse e clica na posição especificada."""
        mouse_util.mover(self.handle, x, y)
        time.sleep(delay)
        mouse_util.clickEsquerdo(self.handle)
