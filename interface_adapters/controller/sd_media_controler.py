import random
import time

import win32api
from PIL import Image

from utils import mouse_util, buscar_item_util, screenshot_util, acao_menu_util
from utils.buscar_item_util import BuscarItemUtil
from utils.mover_spot_util import MoverSpotUtil


class SdMediaController:
    def __init__(self, handle):
        self.handle = handle

    def execute(self):
        self._iniciar_processo()

    def _iniciar_processo(self):
        """Inicia o processo de combinar itens e mover SDs."""
        MoverSpotUtil(self.handle).movimentar_noria((181, 102))
        self._combinar_complex()
        self._agrupar_sd()
        exit()

    def _combinar_complex(self):
        """Combina itens enquanto houver itens para combinar."""
        while True:
            if not self._preparar_combinar():
                acao_menu_util.clicar_inventario(self.handle)
                break

    def _preparar_combinar(self):
        """Prepara o processo de combinação de itens."""
        self._clicar_na_cm()
        self._clicar_na_opcao_combinar_item_regular()
        return self._mover_complex_para_cm()

    def _clicar_na_cm(self):
        while True:
            screenshot_cm = screenshot_util.capture_window(self.handle)
            image_positions = buscar_item_util.buscar_posicoes_item_epecifico(
                './static/inventario/combinacaoarmachaos.png', screenshot_cm)
            if image_positions:
                break
            else:
                mouse_util.left_clique(self.handle, 390, 180)

    def _clicar_na_opcao_combinar_item_regular(self):
        self.clicar_na_imagem_ou_fallback('./static/inventario/combinacaoregular.png', (380, 195))

    def clicar_na_imagem_ou_fallback(self, imagem_path, fallback_position, timeout=60):
        mouse_util.mover(self.handle, 1, 1)
        start_time = time.time()
        while time.time() - start_time < timeout:
            posicao = BuscarItemUtil(self.handle).buscar_item_simples(imagem_path)
            if posicao:
                self.mover_click(*posicao)
                return True
            else:
                if fallback_position:
                    self.mover_click(*fallback_position)
        return False

    def mover_click(self, x, y):
        mouse_util.mover(self.handle, x, y)
        time.sleep(0.045)
        mouse_util.clickEsquerdo(self.handle, delay=0.04)
        time.sleep(0.045)

    def _mover_complex_para_cm(self):
        """Move o item complexo para a área de combinação."""
        achou = self._mover_e_clicar_na_opcao('./static/inventario/complexsmall.png')
        if achou:
            x, y = self._campo_na_cm_para_mover_cp()
            mouse_util.mover_click(self.handle, x, y, delay=.25)  # Move para CM
            self._clicar_na_opcao_processar()
            self._mover_sd_para_invenario()
        return achou

    def _campo_na_cm_para_mover_cp(self):
        """Seleciona um campo aleatório na área de combinação."""
        while True:
            n = random.randint(0, 29)
            count = 0
            screenshot_cm = screenshot_util.capture_window(self.handle)
            image_positions = buscar_item_util.buscar_posicoes_item_epecifico(
                './static/inventario/campovazio.png', screenshot_cm)

            if image_positions:
                for image in image_positions:
                    count += 1
                    if count == n:
                        return image[0], image[1]


    def _clicar_na_opcao_processar(self):
        self.clicar_na_imagem_ou_fallback('./static/inventario/combinar.png', None)
        self.clicar_na_imagem_ou_fallback('./static/inventario/ok.png', None)

    def _mover_sd_para_invenario(self):
        while True:
            screenshot_cm = screenshot_util.capture_window(self.handle)

            cm_vazio = buscar_item_util.buscar_posicoes_item_epecifico('./static/inventario/todoscamposvazioscm.png',
                                                                       screenshot_cm, confidence_=0.99)
            if cm_vazio:
                break

            image_sd = buscar_item_util.buscar_posicoes_item_epecifico('./static/inventario/sdmedia.png', screenshot_cm,
                                                                       confidence_=0.9)
            if image_sd:
                x, y = image_sd[0]
                if x < 590:
                    mouse_util.mover_click(self.handle, x, y)
                    self._mover_para_inventario(screenshot_cm)
                    break

        acao_menu_util.clicar_inventario(self.handle)

    def _mover_para_inventario(self, screenshot_cm):
        """Move o SD para um campo vazio no inventário."""
        image_positions = buscar_item_util.buscar_posicoes_item_epecifico(
            './static/inventario/campovazioinventario.png', screenshot_cm)

        if image_positions:
            for image in image_positions:
                x, y = image
                if x >= 590:  # Achou campo no inventário
                    self._mover_click(x, y)  # Move SD para inventário
                    break

    def _agrupar_sd(self):
        acao_menu_util.clicar_inventario(self.handle)
        time.sleep(1)

        while True:
            mouse_util.mover(self.handle, 1, 1)
            time.sleep(.1)
            screenshot_cm = screenshot_util.capture_window(self.handle)
            todosSds = buscar_item_util.buscar_posicoes_item_epecifico(
                './static/inventario/sdmedia.png', screenshot_cm, confidence_=0.9)

            todosSds10 = buscar_item_util.buscar_posicoes_item_epecifico(
                './static/inventario/sdmedia10.png', screenshot_cm, confidence_=0.9)

            if (todosSds is None or len(todosSds) <= 4) or (todosSds10 and (len(todosSds) - len(todosSds10)) <= 1):
                break

            xAnterior, yAnterior = None, None
            for sd in todosSds:
                xAtual, yAtual = sd
                mouse_util.mover(self.handle, xAtual, yAtual)

                if self._verifica_se_sd_cheio():
                    continue

                if xAnterior is not None and yAnterior is not None:
                    self._mover_click(xAtual, yAtual)
                    self._mover_click(xAnterior, yAnterior)
                    if self._verifica_se_sd_cheio():
                        xAnterior, yAnterior = xAtual, yAtual
                else:
                    xAnterior, yAnterior = xAtual, yAtual

        acao_menu_util.clicar_inventario(self.handle)

    def _verifica_se_sd_cheio(self):
        time.sleep(.1)
        screenshot_cm = screenshot_util.capture_window(self.handle)
        return buscar_item_util.buscar_posicoes_item_epecifico(
            './static/inventario/qtd10.png',
            screenshot_cm, confidence_=0.80)

    def _mover_click(self, x, y, delay=0.1):
        """Move o mouse e clica na posição especificada."""
        mouse_util.mover(self.handle, x, y)
        time.sleep(delay)
        mouse_util.clickEsquerdo(self.handle)

    def _mover_e_clicar_na_opcao(self, img):
        try:
            mouse_util.mover(self.handle, 0, 0)
            start_time = time.time()
            while time.time() - start_time < 3:
                screenshot_cm = screenshot_util.capture_window(self.handle)
                image_positions = buscar_item_util.buscar_posicoes_item_epecifico(img, screenshot_cm, confidence_=0.9)

                if image_positions:
                    x = image_positions[0][0]
                    y = image_positions[0][1]
                    mouse_util.mover_click(self.handle, x, y)
                    time.sleep(.05)
                    return True
        except:
            print('NAO ACHOU: ' + img)
            self._mover_e_clicar_na_opcao(img)
        return False
