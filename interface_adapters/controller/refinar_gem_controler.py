import random
import time

from interface_adapters.controller.BaseController import BaseController
from utils import mouse_util, buscar_item_util, screenshot_util, acao_menu_util
from utils.buscar_item_util import BuscarItemUtil
from utils.pointer_util import Pointers
from utils.teclado_util import Teclado_util


class RefinarGemstoneController(BaseController):

    def _prepare(self):
        self.teclado_util = Teclado_util()
        self.pointers = Pointers()
        self.tempo = .5
        self.pos_y_ultima_joh = 0
        self.pos_x_ultima_joh = 0
        self.qtd_falha = 0

    def _run(self):
        # MoverSpotUtil().movimentar((75, 177))
        self.refinar()

    def refinar(self):
        while True:
            if not self._preparar_combinar():
                acao_menu_util.pressionar_painel_inventario(self.handle)
                # self.teclado_util.escrever_texto('/move noria')
                # exit()

    def _preparar_combinar(self):
        """Prepara o processo de combinação de itens."""
        self._clicar_na_elpis()
        time.sleep(.25)
        self._clicar_na_opcao_refinar_gemstone()
        time.sleep(.25)
        return self._mover_gemstone_para_cm()

    def _clicar_na_elpis(self):
        while True:
            if self.pointers.get_cood_y() == 75 and self.pointers.get_cood_x() == 176:
                self._mover_click(490, 243)  # 75 176
                break
            elif self.pointers.get_cood_y() == 75 and self.pointers.get_cood_x() == 177:
                self._mover_click(487, 242)  # 75, 177
                break
            elif self.pointers.get_cood_y() == 77 and self.pointers.get_cood_x() == 174:
                self._mover_click(490, 200)  # 77 174
                break
            elif self.pointers.get_cood_y() == 74 and self.pointers.get_cood_x() == 177:
                self._mover_click(551, 260)
                break
            elif self.pointers.get_cood_y() == 74 and self.pointers.get_cood_x() == 176:
                self._mover_click(522, 274)
                break
            elif self.pointers.get_cood_y() == 78 and self.pointers.get_cood_x() == 174:
                self._mover_click(444, 161)
                break
            else:
                time.sleep(3)

    def _clicar_na_opcao_refinar_gemstone(self):
        self._mover_click(450, 350)

    def _mover_gemstone_para_cm(self):
        """Move o item gemstone para a área de combinação."""
        image_position = BuscarItemUtil().buscar_item_simples('./static/inventario/gemstone.png')
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

            todoscamposvazioscm = buscar_item_util.buscar_posicoes_item_epecifico(
                './static/inventario/todoscamposvaziorefin.png', screenshot_cm, confidence_=0.95)

            if todoscamposvazioscm:
                break

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

        acao_menu_util.pressionar_painel_inventario(self.handle)

    def _mover_para_inventario(self, screenshot_cm):
        image_positions = buscar_item_util.buscar_posicoes_item_epecifico(
            './static/inventario/campovazioinventario.png', screenshot_cm)

        if image_positions:
            for image in image_positions:
                x, y = image
                if x >= 590:  # Achou campo no inventário
                    self._mover_click(x, y)  # Move joh para inventário
                    break

    def _mover_click(self, x, y, delay=0.15):
        """Move o mouse e clica na posição especificada."""
        mouse_util.mover(self.handle, x, y)
        time.sleep(delay)
        mouse_util.clickEsquerdo(self.handle)
