import ctypes
from ctypes import wintypes

import win32con
import win32gui

from utils import teclado_util

# Constantes
WM_GETTEXT = 0x000D
GWL_STYLE = -16  # Offset para estilos da janela


# Função para obter o texto de um componente
def obter_texto_do_filho(handle):
    buffer = ctypes.create_unicode_buffer(512)
    ctypes.windll.user32.SendMessageW(handle, WM_GETTEXT, 512, ctypes.byref(buffer))
    return buffer.value


# Função para obter a posição e dimensões do componente
def obter_posicao_e_dimensoes(handle):
    rect = ctypes.wintypes.RECT()
    ctypes.windll.user32.GetWindowRect(handle, ctypes.byref(rect))
    return rect.left, rect.top, rect.right, rect.bottom


# Função para obter o nome da classe do componente
def obter_classe_do_filho(handle):
    buffer = ctypes.create_unicode_buffer(512)
    ctypes.windll.user32.GetClassNameW(handle, buffer, 512)
    return buffer.value


# Função para listar todos os filhos e inspecioná-los
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


def encontrar_handle_dialgo(handle):
    handles_filho = listar_e_inspecionar_filhos(handle)
    texto_texte = '/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'

    for handle in handles_filho:
        for char in texto_texte:
            win32gui.SendMessage(handle, win32con.WM_CHAR, ord(char), 0)

        for i, filho in enumerate([handle]):
            classe = obter_classe_do_filho(filho)
            texto = obter_texto_do_filho(filho)
            posicao = obter_posicao_e_dimensoes(filho)
            # print(f"Filho {i + 1}:")
            # print(f"  Handle: {filho}")
            # print(f"  Classe: {classe}")
            # print(f"  Texto: {texto}")
            # print(f"  Posição: {posicao}")
            if len(texto) == 58:
                return filho


def escrever_texto_teste(handles_filho):
    texto_texte = '/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
    for handle in handles_filho:
        for char in texto_texte:
            win32gui.SendMessage(handle, win32con.WM_CHAR, ord(char), 0)

        for i, filho in enumerate([handle]):
            classe = obter_classe_do_filho(filho)
            texto = obter_texto_do_filho(filho)
            posicao = obter_posicao_e_dimensoes(filho)
            # print(f"Filho {i + 1}:")
            # print(f"  Handle: {filho}")
            # print(f"  Classe: {classe}")
            # print(f"  Texto: {texto}")
            # print(f"  Posição: {posicao}")
            if len(texto) == 58:
                return filho


def main():
    window_title = "[1/3] MUCABRASIL"
    handle_pai = find_window_handle_by_partial_title(window_title)
    encontrar_handle_dialgo(handle_pai)


if __name__ == "__main__":
    main()
