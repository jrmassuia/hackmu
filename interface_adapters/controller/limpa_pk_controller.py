import time

import win32gui

from interface_adapters.controller.BaseController import BaseController
from sessao_handle import get_handle_atual
from utils import mouse_util, screenshot_util
from utils.buscar_item_util import BuscarItemUtil
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers


class LimpaPkController(BaseController):

    def _prepare(self):
        self.handle = get_handle_atual()
        self.pointers = Pointers()
        self.mover_spot_util = MoverSpotUtil()
        self.tela = win32gui.GetWindowText(self.handle)

    def _run(self):
        coody = self.pointers.get_cood_y()
        coodx = self.pointers.get_cood_x()
        mousex, mousey = self._localizar_mouse()
        print('Coordenada protegida iniciada! ' + self.tela)
        while True:
            mouse_util.ativar_click_direito(self.handle)
            self.mover_spot_util.movimentar((coody, coodx),
                                            verficar_se_movimentou=True)
            mouse_util.mover(self.handle, mousex, mousey)
            time.sleep(60)

    def _localizar_mouse(self):
        while True:
            screenshot = screenshot_util.capture_window(self.handle)
            # image_position = find_image_in_window(screenshot, './static/img/mouse_mu.png', confidence_threshold=.70)
            image_position = BuscarItemUtil().buscar_imagem_na_janela(screenshot,
                                                                                 './static/img/mouse_mu.png',
                                                                                 precisao=.70)
            if image_position:
                return image_position
