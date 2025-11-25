import random
import time

import win32con
import win32gui

from interface_adapters.controller.BaseController import BaseController
from sessao_handle import get_handle_atual
from utils import mouse_util, buscar_item_util, acao_menu_util, screenshot_util, buscar_coordenada_util, \
    safe_util
from utils.buscar_item_util import BuscarItemUtil
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers
from utils.teclado_util import Teclado_util


def enum_child_windows_callback(handle, lista_de_handles):
    lista_de_handles.append(handle)


def send_text(handle_np, text):
    for char in text:
        win32gui.SendMessage(handle_np, win32con.WM_CHAR, ord(char), 0)


class RefinarPequenaController(BaseController):

    def _prepare(self):
        self.handle = get_handle_atual()
        self.mover_spot_util = MoverSpotUtil()
        self.pointer = Pointers()
        self.teclado_util = Teclado_util()

    def _run(self):

        while True:
            self._mover_noria()
            self._guardar_no_bau()
            self._comprar_spirit_armor()
            self._mover_para_aida()
            self._refinar()

    def _mover_noria(self):
        if safe_util.noria(self.handle) is False:
            self.teclado_util.escrever_texto('/move noria')
            time.sleep(1)

    def _guardar_no_bau(self):
        self._mover_coordenada(172, 95)
        mouse_util.left_clique(self.handle, 420, 196)

        screenshot_cm = screenshot_util.capture_window(self.handle)
        refigns = buscar_item_util.buscar_posicoes_item_epecifico(
            './static/inventario/refinipequena.png', screenshot_cm, confidence_=0.9)

        if refigns:
            for ref in refigns:
                xAtual, yAtual = ref
                if xAtual > 580:
                    mouse_util.right_clique(self.handle, xAtual, yAtual)

        self._retirar_zen()

        acao_menu_util.clicar_inventario(self.handle)

    def _retirar_zen(self):
        mouse_util.left_clique(self.handle, 436, 502)  # clilca no retirar
        time.sleep(.5)
        handles_filhos = []
        win32gui.EnumChildWindows(self.handle, enum_child_windows_callback, handles_filhos)
        send_text(handles_filhos[len(handles_filhos) - 1], '250000000')
        self._mover_e_clicar_na_opcao('./static/inventario/ok.png')
        time.sleep(.5)
        image_position = BuscarItemUtil().buscar_item_simples('./static/inventario/okaviso.png')
        if image_position:
            cpX, cpY = image_position
            mouse_util.left_clique(self.handle, cpX, cpY)  # Clica no ok se tiver pouco zen

    def _comprar_spirit_armor(self):
        self._mover_coordenada(174, 121)
        mouse_util.left_clique(self.handle, 470, 101)  # CLINA NPC
        mouse_util.mover(self.handle, 100, 100)  # Tira o mouse da frente da loja
        while True:
            image_position = BuscarItemUtil().buscar_item_simples('./static/inventario/spiritarmor.png')
            if image_position:
                cpX, cpY = image_position
                for i in range(16):
                    mouse_util.left_clique(self.handle, cpX, cpY)  # Clica na 'spiritarmor'
                break

        acao_menu_util.clicar_inventario(self.handle)

    def _mover_para_aida(self):
        self.mover_spot_util.movimentar((161, 77))
        self.mover_spot_util.movimentar((222, 44))
        self._mover_coordenada(222, 36)  # move para portal
        mouse_util.left_clique(self.handle, 125, 441)
        time.sleep(3)

    def _mover_coordenada(self, y, x, mapa='noria'):
        while True:
            if mapa == 'noria':
                self.mover_spot_util.movimentar((y, x), max_tempo=160)
            else:
                self.mover_spot_util.movimentar((y, x), max_tempo=160)
            time.sleep(.5)
            if x == self.pointer.get_cood_x() and y == self.pointer.get_cood_y():
                time.sleep(.5)
                break

    def _refinar(self):
        self._mover_coordenada(78, 11, mapa='aida')
        while True:
            if not self._preparar_refinar():
                acao_menu_util.clicar_inventario(self.handle)
                break

    def _preparar_refinar(self):
        mouse_util.left_clique(self.handle, 450, 200)  # Clica no goblin
        self._mover_e_clicar_na_opcao('./static/inventario/okaviso.png')
        return self._mover_item_para_refinar()

    def _mover_item_para_refinar(self):
        image_position = BuscarItemUtil().buscar_item_simples('./static/inventario/spiritarmor.png')
        if image_position:
            cpX, cpY = image_position
            mouse_util.mover_click(self.handle, cpX, cpY)  # Clica no 'gladius'
            # x, y = self._campo_na_cm_para_mover_cp()
            coordenadas = [
                (376, 161),
                (413, 152),
                (460, 158),
                (512, 158),
                (358, 201),
                (413, 202),
                (458, 201),
                (505, 200)
            ]
            x, y = random.choice(coordenadas)
            mouse_util.left_clique(self.handle, x, y)  # Move para CM
            self._clicar_na_opcao_processar()
            self._mover_item_para_invenario()
            return True
        return False

    def _campo_na_cm_para_mover_cp(self):
        n = random.randint(11, 19)
        count = 0
        screenshot_cm = screenshot_util.capture_window(self.handle)
        image_positions = buscar_item_util.buscar_posicoes_item_epecifico(
            './static/inventario/campovazio.png', screenshot_cm, confidence_=0.80)

        if image_positions:
            for image in image_positions:
                count += 1
                if count == n:
                    return image[0], image[1]
        return None, None

    def _mover_item_para_invenario(self):
        while True:
            screenshot_cm = screenshot_util.capture_window(self.handle)

            todoscamposvazioscm = buscar_item_util.buscar_posicoes_item_epecifico(
                './static/inventario/todoscamposvazioscm.png', screenshot_cm, confidence_=0.95)

            if todoscamposvazioscm:
                break

            image_positions = buscar_item_util.buscar_posicoes_item_epecifico(
                './static/inventario/refinipequena.png', screenshot_cm, confidence_=0.75)

            if image_positions:
                x, y = image_positions[0]
                if x < 590:
                    mouse_util.mover_click(self.handle, x, y)  # Clica no SD
                    self._mover_para_inventario(screenshot_cm)
                    break

        acao_menu_util.clicar_inventario(self.handle)

    def _mover_para_inventario(self, screenshot_cm):
        image_positions = buscar_item_util.buscar_posicoes_item_epecifico(
            './static/inventario/campovazioinventario.png', screenshot_cm)

        if image_positions:
            for image in image_positions:
                x, y = image
                if x >= 590:  # Achou campo no inventário
                    mouse_util.mover_click(self.handle, x, y)  # Move joh para inventário
                    break

    def _clicar_na_opcao_processar(self):
        """Clica nas opções para processar a combinação."""
        self._mover_e_clicar_na_opcao('./static/inventario/combinar.png')
        time.sleep(.5)
        self._mover_e_clicar_na_opcao('./static/inventario/ok.png')

    def _mover_e_clicar_na_opcao(self, imagem_path, timeout=60):
        mouse_util.mover(self.handle, 1, 1)
        start_time = time.time()
        achou = False
        while time.time() - start_time < timeout:
            posicao = BuscarItemUtil().buscar_item_simples(imagem_path)

            if achou and posicao is None:
                return True
            else:
                achou = False

            if posicao:
                mouse_util.left_clique(self.handle, *posicao)
                achou = True

        return False
        # try:
        #     mouse_util.mover(self.handle, 0, 0)
        #     time.sleep(.1)
        #     while True:
        #         # local = self._localizar_em_multiplos_monitores(Image.open(img), confidence=0.70)
        #         screenshot_cm = screenshot_util.capture_window(self.handle)
        #         image_positions = buscar_item_util.buscar_posicoes_item_epecifico(img, screenshot_cm, confidence_=0.9)
        #
        #         if image_positions:
        #             x = image_positions[0][0]
        #             y = image_positions[0][1]
        #             mouse_util.mover_click(self.handle, x, y)
        #             break
        #         else:
        #             time.sleep(0.5)
        # except:
        #     print('NAO ACHOU: ' + img)
        #     self._mover_e_clicar_na_opcao(img)

    def _esta_na_safe_aida(self):
        ycood, xcood = buscar_coordenada_util.coordernada(self.handle)
        return (xcood and ycood) and ((5 <= xcood <= 17) and (75 <= ycood <= 92))
