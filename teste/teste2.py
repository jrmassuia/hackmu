import cv2
import keyboard
import numpy as np
import ctypes
import os
import random
import time
from ctypes import wintypes
from ctypes.wintypes import HWND, WPARAM, LPARAM
import ctypes
import time
from typing import Iterable
import time

import pydirectinput as pydirectinput
import win32com.client as comclt
import win32gui
import win32api
from pynput.keyboard import Key, Controller
import psutil
import pyautogui
import pydivert
import win32con
import win32gui
import winsound

import MuEntityScannerPK
import testeautopk
from services.buscar_personagem_proximo_service import BuscarPersoangemProximoService
from services.foco_mutex_service import FocoMutexService
from services.verificador_imagem_userbar import VerificadorImagemUseBar
from utils.buscar_item_util import BuscarItemUtil
from utils.mover_spot_util import MoverSpotUtil

kernel32 = ctypes.windll.kernel32
usuario32 = ctypes.windll.user32
import interception
import win32gui
from sympy.codegen.ast import Pointer

from domain.arduino_teclado import Arduino
from interface_adapters.up.up_util import up_util
from utils import teclado_util, mouse_util, spot_util, screenshot_util
from utils.pointer_util import Pointers
from utils.teclado_util import Teclado_util

# Constantes de mensagens para eventos de teclado
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
user32 = ctypes.windll.user32
WM_SETCURSOR = 0x0020
WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205

WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
VK_RETURN = 0x0D

HTCLIENT = 1  # Hit-test no cliente da janela
MK_LBUTTON = 0x0001  # Botão esquerdo pressionado
MK_RBUTTON = 0x0002  # Botão direito pressionado
VK_CODES = {
    **{str(i): 0x30 + i for i in range(10)},  # Teclas numéricas 0-9
    **{chr(i): i for i in range(0x41, 0x5A + 1)},  # Letras A-Z
    **{f"F{i}": 0x70 + (i - 1) for i in range(1, 13)},  # Teclas F1-F12
    "ALT": 0x12,
    "SHIFT": 0x10,
    "CTRL": 0x11,
    "ENTER": 0x0D,
    "BACKSPACE": 0x08,
    "SPACE": 0x20,
    "TAB": 0x09,
    "ESC": 0x1B,
}

# Carregar a biblioteca user32.dll
user32 = ctypes.windll.user32


def find_window_handle_by_partial_title(partial_title):
    # Callback para encontrar a janela pelo título parcial
    def enum_windows_callback(hwnd, handles):
        if partial_title in win32gui.GetWindowText(hwnd):
            handles.append(hwnd)

    # Lista para armazenar os handles encontrados
    handles = []
    win32gui.EnumWindows(enum_windows_callback, handles)
    # Retorna o primeiro handle encontrado ou None
    return handles[0] if handles else None


def make_lparam(x: int, y: int) -> LPARAM:
    return LPARAM(y << 16 | x & 0xFFFF)


def _buscar_spots():
    return [
        [['SM', 'MG'], [(178, 38), (182, 15)], (398, 240)], [['DL'], [(178, 38), (185, 11)], (403, 128)],
    ]


def obter_portas_do_processo(nome_exe):
    portas = []
    for conn in psutil.net_connections(kind='inet'):
        try:
            proc = psutil.Process(conn.pid)
            if proc.name().lower() == nome_exe.lower() and conn.laddr and conn.laddr.port:
                portas.append(conn.laddr.port)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return list(set(portas))  # remove duplicadas


def delay_por_processo(nome_exe="mucabrasil.exe", delay=3):
    portas = obter_portas_do_processo(nome_exe)
    if not portas:
        print(f"Nenhuma porta encontrada para {nome_exe}")
        return

    filtro = " or ".join([f"tcp.SrcPort == {p} or tcp.DstPort == {p}" for p in portas])
    print(f"Aplicando delay em {nome_exe} portas {portas}...")

    with pydivert.WinDivert(filtro) as w:
        cont = 0
        for pacote in w:
            if cont == 2:
                time.sleep(delay)
                exit()
            cont = cont + 1
            w.send(pacote)
            # print(f"Pacote {pacote} atrasado {delay}s")


def main():
    print("Selecione a tela do Mu:\n")
    print("1 - [1/3] MUCABRASIL")
    print("2 - [2/3] MUCABRASIL")
    print("3 - [3/3] MUCABRASIL\n")

    while True:
        try:
            escolha = int(input("Digite o número da tela (1 a 3): "))
            if escolha in [1, 2, 3]:
                break
            else:
                print("Valor inválido. Escolha entre 1, 2 ou 3.")
        except ValueError:
            print("Digite um número válido.")

    window_title = f"[{escolha}/3] MUCABRASIL"
    handle = find_window_handle_by_partial_title(window_title)
    pointer = Pointers(hwnd=handle).teste_pointer_necessarios()


def pressionar_tecla(tecla: str, delay=0.1) -> None:
    interception.auto_capture_devices()
    with interception.hold_key(tecla):
        time.sleep(delay)

    # mouse_util.left_clique(handle, 482, 25)

    # spots = spot_util.buscar_spots_aida_volta_final(ignorar_spot_pk=True)
    # spots.extend(spot_util.buscar_spots_aida_2(ignorar_spot_pk=True))
    # print(spots)
    #
    # _mover_lost3_para_lost4(handle, pointer)
    # print(BuscarPersoangemProximoService(pointer).listar_nomes_e_coords_por_padrao())

    # buscar_personagem = BuscarPersoangemProximoService(pointer)
    # resultados = BuscarPersoangemProximoService(pointer).listar_nomes_e_coords_por_padrao()
    # print(resultados)

    # personagem_proximo_service = BuscarPersoangemProximoService(pointer)
    #
    # itens = personagem_proximo_service.listar_nomes_e_coords_por_padrao()
    #
    # proximos = personagem_proximo_service.personagem_proximo(itens, limite=10, incluir_dist=True, raio=10,
    #                                                          exigir_nome=True)
    # for addr, x, y, nome, dist in proximos:
    #     print(f"{nome or '<sem-nome>'}  X={x} Y={y}")


def _mover_lost1_para_lost2(handle, pointer):
    _posicionar_mover_pelo_portal(handle, pointer, 195, 7)
    mouse_util.left_clique(handle, 228, 131)


def _mover_lost2_para_lost3(handle, pointer):
    _posicionar_mover_pelo_portal(handle, pointer, 164, 170)
    mouse_util.left_clique(handle, 194, 395)


def _mover_lost3_para_lost4(handle, pointer):
    _posicionar_mover_pelo_portal(handle, pointer, 130, 247)
    mouse_util.left_clique(handle, 529, 321)


def _mover_lost4_para_lost5(handle, pointer):
    _posicionar_mover_pelo_portal(handle, pointer, 134, 133)
    # mouse_util.left_clique(handle, , )


def _mover_lost5_para_lost6(handle, pointer):
    _posicionar_mover_pelo_portal(handle, pointer, 130, 21)
    # mouse_util.left_clique(handle, , )


def _mover_lost6_para_lost7(handle, pointer):
    _posicionar_mover_pelo_portal(handle, pointer, 9, 6)
    # mouse_util.left_clique(handle, , )


def _mover_lost7_para_icarus(handle, pointer):
    _posicionar_mover_pelo_portal(handle, pointer, 18, 249)
    # mouse_util.left_clique(handle, , )


def _posicionar_mover_pelo_portal(handle, pointer, y, x):
    while True:
        MoverSpotUtil(handle).movimentar((y, x), max_tempo=100000)
        time.sleep(.5)
        if x == pointer.get_cood_x() and y == pointer.get_cood_y():
            time.sleep(.5)
            break


def send(hwnd: int, command: str):
    vk_code = VK_CODES.get(command.upper())
    if vk_code is None:
        raise ValueError(f"Tecla '{command}' não é suportada ou inválida.")

    # Envia as mensagens WM_KEYDOWN e WM_KEYUP
    user32.SendMessageW(HWND(hwnd), WM_KEYDOWN, WPARAM(vk_code), LPARAM(0))
    user32.SendMessageW(HWND(hwnd), WM_KEYUP, WPARAM(vk_code), LPARAM(0))


def encontrar_filho(handle_pai, criterio_func):
    """
    Encontra o filho específico dentro dos filhos de um handle pai.

    :param handle_pai: O handle do pai que contém os filhos.
    :param criterio_func: Uma função que verifica se o filho é o desejado.
    :return: O handle do filho correspondente, ou None se não for encontrado.
    """
    filhos = obter_filhos_do_handle(handle_pai)  # Exemplo: uma função para obter os filhos
    for filho in filhos:
        if criterio_func(filho):  # Verifica o critério para encontrar o filho
            return filho
    return None


def obter_titulo_do_filho(handle):
    try:
        WM_GETTEXT = 0x000D
        buffer = ctypes.create_unicode_buffer(512)
        ctypes.windll.user32.SendMessageW(handle, WM_GETTEXT, 512, ctypes.byref(buffer))
        return buffer.value
    except:
        return ""


def listar_e_inspecionar_filhos(handle_pai):
    filhos = []

    def enum_callback(handle, lparam):
        filhos.append(handle)
        return True

    ENUM_CHILD_WINDOWS = ctypes.WINFUNCTYPE(
        wintypes.BOOL, wintypes.HWND, wintypes.LPARAM
    )
    enum_proc = ENUM_CHILD_WINDOWS(enum_callback)
    ctypes.windll.user32.EnumChildWindows(handle_pai, enum_proc, 0)
    return filhos


def obter_filhos_do_handle(handle_pai):
    filhos = []

    def enum_callback(handle, lparam):
        filhos.append(handle)
        return True

    ENUM_CHILD_WINDOWS = ctypes.WINFUNCTYPE(
        wintypes.BOOL, wintypes.HWND, wintypes.LPARAM
    )
    enum_proc = ENUM_CHILD_WINDOWS(enum_callback)
    ctypes.windll.user32.EnumChildWindows(handle_pai, enum_proc, 0)
    return filhos


if __name__ == "__main__":
    main()
