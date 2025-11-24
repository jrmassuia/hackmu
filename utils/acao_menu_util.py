import time

from utils import mouse_util, screenshot_util, buscar_item_util
from utils.teclado_util import Teclado_util


def pressionar_painel_comando(handle):
    Teclado_util(handle).tap_tecla('D')


def pressionar_painel_inventario(handle):
    Teclado_util(handle).tap_tecla('V')


def clicar_inventario(handle):
    mouse_util.left_clique(handle, 525, 580)


def clicar_loja(handle):
    mouse_util.mover(handle, 1, 1)
    mouse_util.left_clique(handle, 684, 506)


def clicar_txt_loja(handle):
    mouse_util.left_clique(handle, 447, 97)


def clicar_personagemC(handle):
    mouse_util.left_clique(handle, 490, 580, delay=.5)


def fechar_inventario(handle):
    if _inventario_aberto(handle):
        aberto = False
        while True:
            screenshot_cm = screenshot_util.capture_window(handle)
            image_positions = buscar_item_util.buscar_posicoes_item_epecifico(
                './static/inventario/fecharinventario.png', screenshot_cm)
            if aberto:
                break
            if image_positions:
                mouse_util.left_clique(handle, 525, 580)
                aberto = True


def _inventario_aberto(handle):
    qtd = 0
    while True:
        screenshot_cm = screenshot_util.capture_window(handle)
        image_positions = buscar_item_util.buscar_posicoes_item_epecifico(
            './static/inventario/fecharinventario.png', screenshot_cm)
        if image_positions is not None:
            return True
        else:
            qtd = qtd + 1
            time.sleep(.1)
            if qtd > 5:
                return False
