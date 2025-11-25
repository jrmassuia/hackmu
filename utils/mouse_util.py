import ctypes
import time
from ctypes import wintypes
from ctypes.wintypes import HWND, WPARAM, LPARAM

import win32api
import win32con
import win32gui

from utils import buscar_item_util
from utils.buscar_item_util import BuscarItemUtil

user32 = ctypes.windll.user32

# Constantes das mensagens
WM_SETCURSOR = 0x0020
WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205

HTCLIENT = 1  # Hit-test no cliente da janela
MK_LBUTTON = 0x0001  # Botão esquerdo pressionado
MK_RBUTTON = 0x0002  # Botão direito pressionado

def make_lparam(x: int, y: int) -> LPARAM:
    return LPARAM(y << 16 | x & 0xFFFF)


def left_clique(hwnd: int, x: int, y: int, delay=0.1):
    user32.SendMessageW(HWND(hwnd), WM_SETCURSOR, WPARAM(hwnd), LPARAM(HTCLIENT | (WM_MOUSEMOVE << 16)))
    user32.SendMessageW(HWND(hwnd), WM_MOUSEMOVE, WPARAM(0), make_lparam(x, y))
    time.sleep(.5)
    user32.SendMessageW(HWND(hwnd), WM_LBUTTONDOWN, WPARAM(MK_LBUTTON), make_lparam(x, y))
    time.sleep(delay)
    user32.SendMessageW(HWND(hwnd), WM_LBUTTONUP, WPARAM(0), make_lparam(x, y))
    time.sleep(.5)


def right_clique(hwnd: int, x: int, y: int, delay=0.1):
    user32.SendMessageW(HWND(hwnd), WM_SETCURSOR, WPARAM(hwnd), LPARAM(HTCLIENT | (WM_MOUSEMOVE << 16)))
    user32.SendMessageW(HWND(hwnd), WM_MOUSEMOVE, WPARAM(0), make_lparam(x, y))
    time.sleep(.5)
    user32.SendMessageW(HWND(hwnd), WM_RBUTTONDOWN, WPARAM(MK_RBUTTON), make_lparam(x, y))
    time.sleep(delay)
    user32.SendMessageW(HWND(hwnd), WM_RBUTTONUP, WPARAM(0), make_lparam(x, y))
    time.sleep(.5)


def clickEsquerdo(handle, delay=0.3):
    win32gui.PostMessage(handle, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, None)
    time.sleep(delay)
    win32gui.PostMessage(handle, win32con.WM_LBUTTONUP, None, None)


def forcarClickEsquerdo(handle):
    win32gui.SetForegroundWindow(handle)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)  # Pequeno atraso para simular clique real
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def ativar_click_esquerdo(handle):
    win32gui.PostMessage(handle, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, None)


def desativar_click_esquerdo(handle):
    win32gui.PostMessage(handle, win32con.WM_LBUTTONUP, None, None)


def ativar_click_direito(handle):
    win32gui.PostMessage(handle, win32con.WM_RBUTTONDOWN, win32con.MK_LBUTTON, None)


def desativar_click_direito(handle):
    win32gui.PostMessage(handle, win32con.WM_RBUTTONUP, None, None)


def clickDireito(handle):
    win32gui.PostMessage(handle, win32con.WM_RBUTTONDOWN, win32con.MK_LBUTTON, None)
    time.sleep(0.3)
    win32gui.PostMessage(handle, win32con.WM_RBUTTONUP, None, None)


def zoonTela(handle):
    mover_mouse_centro_no_handle(handle)
    time.sleep(.5)
    for _ in range(5):
        win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, -120, 0)
        time.sleep(0.05)
    win32api.SetCursorPos((1, 1))


def mover(handle, x, y):
    position = make_long(x, y)
    win32gui.PostMessage(handle, win32con.WM_MOUSEMOVE, 0, position)


def make_long(x, y):
    return win32api.MAKELONG(x, y)


def moverClickEsquerdo(handle, x, y):
    mover(handle, x, y)
    time.sleep(0.3)
    clickEsquerdo(handle)
    time.sleep(0.1)
    moverCentro(handle)


def mover_click(handle, x, y, delay=0.1):
    mover(handle, x, y)
    time.sleep(delay)
    clickEsquerdo(handle)


def moverCentro(handle):
    user32.SendMessageW(HWND(handle), WM_SETCURSOR, WPARAM(handle), LPARAM(HTCLIENT | (WM_MOUSEMOVE << 16)))
    user32.SendMessageW(HWND(handle), WM_MOUSEMOVE, WPARAM(0), make_lparam(400, 255))


def obter_posicao_do_handle(handle):
    """
    Retorna as coordenadas de um handle na tela.
    :param handle: Handle do componente.
    :return: (x, y, largura, altura)
    """
    rect = wintypes.RECT()
    ctypes.windll.user32.GetWindowRect(handle, ctypes.byref(rect))
    return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top


def mover_mouse_centro_no_handle(handle):
    """
    Move o mouse para o handle e realiza um clique com o botão esquerdo.
    :param handle: Handle do componente.
    """
    # Obter as coordenadas do handle
    left, top, largura, altura = obter_posicao_do_handle(handle)

    # Calcula o centro do componente para o clique
    x = left + largura // 2
    y = top + altura // 2

    # Move o mouse para a posição do handle
    win32api.SetCursorPos((x, y))


def tira_mouse_tela(handle):
    mover(handle, 1, 1)


def clicar_na_imagem_ou_coordenada(handle, imagem_path, fallback_position, timeout=5):
    try:
        start_time = time.time()
        while time.time() - start_time < timeout:
            posicao = BuscarItemUtil().buscar_item_simples(imagem_path)
            if posicao:
                left_clique(handle, *posicao, delay=.5)
                return True
            elif fallback_position is not None:
                left_clique(handle, *fallback_position)
        return False
    except:
        return False
