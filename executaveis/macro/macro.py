import time

import keyboard
import win32api
import win32con
import win32gui

from utils import teclado_util
from utils.pointer_util import Pointers

regiao = (183, 935, 2, 2)
colors = [(130, 52, 9),
          # (134, 54, 11),
          # (184, 73, 13),
          (193, 77, 16)]

# Variável para controlar se a verificação do botão direito está ativa
verificacao_botao_direito_ativa = True


# Função para alternar a verificação do botão direito com a tecla 'r'
def toggle_verificacao(event):
    global verificacao_botao_direito_ativa
    verificacao_botao_direito_ativa = not verificacao_botao_direito_ativa
    status = "ATIVADO" if verificacao_botao_direito_ativa else "DESATIVADO"
    print(f"{status} - Botão direito")


# Registrar as funções para as teclas Q, W e V
keyboard.on_press_key('9', toggle_verificacao)  # Ativar/desativar a vvverificação do botão direito


# Loop principal
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


window_title = "[1/3] MUCABRASIL"
handle = find_window_handle_by_partial_title(window_title)
pointers = Pointers(handle)
ponto_sd = None
ponto_hp = None
limite_sd_95 = 0
limite_sd_50 = 0
limite_hp_20 = 0
tempo_segundo = 1.0
numero_de_potes = 4
total_interacoes = numero_de_potes * 2

# SO FUNCIONA COM MS 20MS
while True:

    inicio_ciclo = time.time()

    if verificacao_botao_direito_ativa:

        if win32api.GetKeyState(win32con.VK_SPACE) < 0 or win32api.GetKeyState(win32con.VK_RBUTTON) < 0:

            if ponto_sd is None:
                ponto_sd = pointers.get_sd()
                ponto_hp = pointers.get_hp()
                limite_sd_95 = ponto_sd * 0.95
                limite_sd_50 = ponto_sd * 0.50
                limite_hp_20 = ponto_hp * 0.20

            delay_tecla = .07
            delay_entre_tecla = .052
            for i in range(numero_de_potes):

                teclado_util.pressionar_tecla("q", delay=delay_tecla) # Pota COMPLEX
                time.sleep(delay_entre_tecla)  # Delay entre Q e W

                if limite_sd_95 >= pointers.get_sd():
                    # Pota SD
                    teclado_util. pressionar_tecla("w", delay=delay_tecla) # Pota SD SMALL
                else:
                    # POTA HP
                    teclado_util. pressionar_tecla("e", delay=delay_tecla) # Pota HP
                time.sleep(delay_entre_tecla)

            # Tempo total gasto no ciclo
            tempo_gasto = time.time() - inicio_ciclo

            # Calcular o tempo médio necessário para cada interação
            tempo_medio_por_interacao = tempo_segundo / total_interacoes  # 1 segundo dividido pelas 8 interações
            tempo_alvo = tempo_medio_por_interacao * total_interacoes

            # Tempo restante para completar o ciclo em 1 segundo
            tempo_restante = tempo_alvo - tempo_gasto

            # Se o tempo restante for positivo, faz uma pausa para completar o ciclo de 1 segundo
            print('Tempo resante: ' + str(tempo_restante))
            if tempo_restante > 0:
                time.sleep(tempo_restante)

            # detector = RegionColorDetector(handle, regiao, colors)
            # resultado = detector.detect_colors()

            # teclado_util. pressionar_tecla(teclado_util.VK_Q, delay=.06)
            # time.sleep(.047)
            #
            # teclado_util. pressionar_tecla(teclado_util.VK_W, delay=.06)
            # time.sleep(.047)

            # # resultado = True  - SD CHEIO
            # ## POTA COMPLEX E HPqwq
            # if resultado:
            #     teclado_util. pressionar_tecla(teclado_util.VK_Q, delay=.078)
            #     time.sleep(.05)
            #
            #     teclado_util. pressionar_tecla(teclado_util.VK_E, delay=.078)
            #     time.sleep(.05)
            #
            # # resultado = False  - SD VAZIO
            # ## POTA COMPLEX E SD
            # else:
            #     teclado_util. pressionar_tecla(teclado_util.VK_Q, delay=.06)
            #     time.sleep(.045)
            #
            #     teclado_util. pressionar_tecla(teclado_util.VK_W, delay=.06)qwqw
            #     time.sleep(.045)
