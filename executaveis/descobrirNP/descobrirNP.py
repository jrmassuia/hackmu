import time
from itertools import product

import win32con
import win32gui

from utils import mouse_util, buscar_item_util
from utils.buscar_item_util import BuscarItemUtil


def gerar_senhas():
    """Gera e testa combinações de senhas de 7 dígitos."""
    window_title = "[2/3] MUCABRASIL"
    handle = find_window_handle_by_partial_title(window_title)
    handle_np = None

    if not handle:
        print(f"Janela com o título parcial '{window_title}' não encontrada.")
        return

        # mover_click(handle, 670, 450)
        # time.sleep(.5)
        # Gera todas as combinações possíveis de 7 dígitos (0000000 a 9999999)
        # for senha in product("0123456789", repeat=7):
    senhas = senhas = [''.join(s) for s in reversed(list(product("0123456789", repeat=7)))]
    for senha in senhas:
        print(f"Testando número pessoal: {senha}")
        inicio = time.perf_counter()

        # Tenta clicar no botão "OK"
        if not clicar_na_imagem_ou_fallback(handle, "../../static/numpessoal/botaoretirar.png", (670, 450)):
            print("Erro ao clicar no botão OK. Continuando...")
            continue

        # # Digita a senha no campo
        # if not esperar_por_imagem_e_executar(handle, "../../static/numpessoal/camponp.png",
        #                                      lambda: send_text(handle_np, senhacompleta)):
        #     print("Erro ao encontrar o campo de número pessoal.")
        #     continue

        handles_filhos = []
        win32gui.EnumChildWindows(handle, enum_child_windows_callback, handles_filhos)
        send_text(handles_filhos[len(handles_filhos) - 1], senha)

        # # Tenta clicar no botão "Ok"
        if not clicar_na_imagem_ou_fallback(handle, "../../static/numpessoal/botaook.png", (330, 260)):
            print("Erro ao clicar no botão Cancelar.")
            continue

        # mover_click(handle, 320, 260) OK

        # Verifica se a senha foi aceita
        if not BuscarItemUtil(handle).buscar_item_simples("../../static/numpessoal/botaoretirar.png"):
            print(f"Senha correta encontrada: {senha}")
            return
        # else:
        #     mover_click(handle, 670, 450)

        fim = time.perf_counter()
        tempo_decorrido = fim - inicio
        print(f"Tempo de processamento (preciso): {tempo_decorrido:.5f} segundos")


def clicar_na_imagem_ou_fallback(handle, imagem_path, fallback_position, timeout=5):
    """
    Clica na posição da imagem encontrada ou na posição de fallback se a imagem não for encontrada.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        posicao = BuscarItemUtil(handle).buscar_item_simples(imagem_path)
        if posicao:
            # mouse_util.moverClickEsquerdo(handle, *posicao)
            mover_click(handle, *posicao)
            return True
        else:
            mover_click(handle, *fallback_position)
    return False


def esperar_por_imagem_e_executar(handle, imagem_path, acao, timeout=5):
    """
    Espera pela imagem especificada e executa uma ação se ela for encontrada.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if BuscarItemUtil(handle).buscar_item_simples(imagem_path):
            acao()
            return True
    return False


def mover_click(handle, x, y):
    """
    Move o mouse para uma posição e clica com o botão esquerdo.
    """
    mouse_util.mover(handle, x, y)
    time.sleep(0.045)
    mouse_util.clickEsquerdo(handle, delay=0.04)
    time.sleep(0.045)


def send_text(handle_np, text):
    for char in text:
        win32gui.SendMessage(handle_np, win32con.WM_CHAR, ord(char), 0)


def enum_child_windows_callback(handle, lista_de_handles):
    lista_de_handles.append(handle)


def find_window_handle_by_partial_title(partial_title):
    """
    Encontra o handle da janela pelo título parcial.
    """

    def enum_windows_callback(hwnd, handles):
        if partial_title in win32gui.GetWindowText(hwnd):
            handles.append(hwnd)

    handles = []
    win32gui.EnumWindows(enum_windows_callback, handles)
    return handles[0] if handles else None


# Exemplo de uso
if __name__ == "__main__":
    gerar_senhas()
