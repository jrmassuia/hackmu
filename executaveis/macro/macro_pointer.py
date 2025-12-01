# import time
#
# import keyboard
# import win32gui
#
# from utils import teclado_util
# from utils.pointer_util import Pointers
#
#
# class MacroPointer:
#     def __init__(self):
#         self.verificacao_ativa = False
#         self.window_title = "[1/3] MUCABRASIL"
#         self.handle = self._find_window_handle()
#         self.pointers = Pointers()
#         self.numero_de_potes = 4
#         self.total_interacoes = self.numero_de_potes * 2
#         self.delay_tecla = 0.05
#         self.delay_entre_tecla = 0.045
#         self.limites_sd = None
#
#         keyboard.on_press_key('F5', self._toggle_verificacao)
#         print("[INFO] Macro inicializado e aguardando F5 para ativar/desativar.")
#
#     def _toggle_verificacao(self, event):
#         self.verificacao_ativa = not self.verificacao_ativa
#         status = "ATIVADO" if self.verificacao_ativa else "DESATIVADO"
#         print(f"{status} - Botão direito")
#
#     def _find_window_handle(self):
#         def enum_windows_callback(hwnd, handles):
#             if self.window_title in win32gui.GetWindowText(hwnd):
#                 handles.append(hwnd)
#
#         handles = []
#         win32gui.EnumWindows(enum_windows_callback, handles)
#         return handles[0] if handles else None
#
#     def _calcular_limites_sd(self, sd_max):
#         self.limites_sd = {
#             "limite_sd_80": int(sd_max * 0.80),
#             "limite_sd_95": int(sd_max * 0.95),
#             "limite_sd_50": int(sd_max * 0.50)
#         }
#
#     def _enviar_tecla(self, vk_code):
#         teclado_util.enviar_tecla(vk_code, delay=self.delay_tecla)
#
#     def _usar_potes_cx_hp_sd(self):
#         for _ in range(self.numero_de_potes):
#             if self.pointers.get_sd() == self.pointers.get_sd_max() and self.pointers.get_hp() == self.pointers.get_hp_max():
#                 print('Vida e SD Cheia!')
#                 return False
#             else:
#                 self._enviar_tecla(teclado_util.VK_Q)  # Pota COMPLEX
#                 time.sleep(self.delay_entre_tecla)
#
#             sd = self.pointers.get_sd()
#
#             if sd >= self.limites_sd["limite_sd_95"]:
#                 self._enviar_tecla(teclado_util.VK_E)  # Pota HP
#             elif sd <= self.limites_sd["limite_sd_80"]:
#                 self._enviar_tecla(teclado_util.VK_W)  # Pota SD Média
#             else:
#                 self._enviar_tecla(teclado_util.VK_R)  # Pota SD Pequena
#
#             time.sleep(self.delay_entre_tecla)
#             return True
#
#     def _usar_potes_cx_sd(self):
#         for _ in range(self.numero_de_potes):
#             self._enviar_tecla(teclado_util.VK_Q)  # Pota COMPLEX/HP
#             time.sleep(self.delay_entre_tecla)
#
#             self._enviar_tecla(teclado_util.VK_W)  # Pota SD Pequena
#             time.sleep(self.delay_entre_tecla)
#
#     def _esperar_proximo_ciclo(self, inicio_ciclo, tempo_segundo=1):
#         tempo_gasto = time.time() - inicio_ciclo
#         tempo_medio_por_interacao = tempo_segundo / self.total_interacoes
#         tempo_alvo = tempo_medio_por_interacao * self.total_interacoes
#         tempo_restante = tempo_alvo - tempo_gasto
#
#         print(f'Tempo restante: {tempo_restante:.3f} segundos')
#         if tempo_restante > 0:
#             time.sleep(tempo_restante)
#
#     def rodar(self):
#         while True:
#             inicio_ciclo = time.time()
#
#             if self.limites_sd is None:
#                 self._calcular_limites_sd(self.pointers.get_sd_max())
#
#             if self.verificacao_ativa:
#                 if (self.pointers.get_sd_max() > self.pointers.get_sd() or
#                         self.pointers.get_hp_max() > self.pointers.get_hp()):
#                     potou = self._usar_potes_cx_hp_sd()
#                     # self._usar_potes_cx_sdq()
#                     if potou:
#                         self._esperar_proximo_ciclo(inicio_ciclo)
#
#
# macro = MacroPointer()
# macro.rodar()

import time

import keyboard
import win32api
import win32con
import win32gui

from utils.pointer_util import Pointers
from utils.teclado_util import Teclado_util

# Variável para controlar se a verificação do botão direito está ativa
verificacao_botao_direito_ativa = False


def toggle_verificacao(event):
    global verificacao_botao_direito_ativa
    verificacao_botao_direito_ativa = not verificacao_botao_direito_ativa
    status = "ATIVADO" if verificacao_botao_direito_ativa else "DESATIVADO"
    print(f"{status} - Botão direito")


keyboard.on_press_key('F5', toggle_verificacao)  # Ativar/desativar a verificação do botão direito
print("[INFO] Macro inicializado e aguardando F5 para ativar/desativar.")


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


def calcular_limites(ponto_sd):
    return {
        "limite_sd_80": int(ponto_sd * 0.80),
        "limite_sd_95": int(ponto_sd * 0.95),
        "limite_sd_50": int(ponto_sd * 0.50)
    }


def usar_potes(numero_de_potes, limites, pointers, teclado):
    delay_tecla = 0.02
    delay_entre_tecla = 0.023

    # if pointers.get_magia() in ['Poison', 'Ice', 'Lighting']:
    #     return

    for _ in range(numero_de_potes):
        if (pointers.get_hp() != pointers.get_hp_max()) or (pointers.get_sd() != pointers.get_sd_max()):
            teclado.toque_arduino("Q", delay=delay_tecla)  # Pota COMPLEX
            time.sleep(delay_entre_tecla)
            teclado.toque_arduino("W", delay=delay_tecla)  # Pota SD MEDIA

        # if pointers.get_sd() >= limites["limite_sd_95"]:
        #     teclado_util.enviar_tecla(teclado_util.VK_E, delay=delay_tecla)  # Pota HP
        # elif pointers.get_sd() <= limites["limite_sd_80"]:
        #     teclado_util.enviar_tecla(teclado_util.VK_W, delay=delay_tecla)  # Pota SD MEDIA
        # else:
        #     teclado_util.enviar_tecla(teclado_util.VK_R, delay=delay_tecla)  # Pota SD SMALL

        # if limites["limite_sd_80"] >= pointers.get_sd():
        #     teclado_util.enviar_tecla(teclado_util.VK_W, delay=delay_tecla)  # Pota SD MEDIA
        # if limites["limite_sd_95"] >= pointers.get_sd():
        #     teclado_util.enviar_tecla(teclado_util.VK_R, delay=delay_tecla)  # Pota SD SMALL
        # else:
        #     teclado_util.enviar_tecla(teclado_util.VK_E, delay=delay_tecla)  # Pota HP

        time.sleep(delay_entre_tecla)


def esperar_proximo_ciclo(inicio_ciclo, total_interacoes, tempo_segundo=1):
    tempo_gasto = time.time() - inicio_ciclo
    tempo_medio_por_interacao = tempo_segundo / total_interacoes
    tempo_alvo = tempo_medio_por_interacao * total_interacoes
    tempo_restante = tempo_alvo - tempo_gasto

    print(f'Tempo restante: {tempo_restante:.3f} segundos')
    if tempo_restante > 0:
        time.sleep(tempo_restante)


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
    pointers = Pointers(hwnd=handle)
    teclado = Teclado_util()

    numero_de_potes = 4
    total_interacoes = numero_de_potes * 2
    ponto_sd = pointers.get_sd_max()
    ponto_hp = pointers.get_hp_max()
    limites = calcular_limites(ponto_sd)
    while True:
        inicio_ciclo = time.time()

        if verificacao_botao_direito_ativa:
            # if ponto_sd > pointers.get_sd() or ponto_hp > pointers.get_hp():
            if win32api.GetAsyncKeyState(win32con.VK_RBUTTON) < 0:
                usar_potes(numero_de_potes, limites, pointers, teclado)
                # esperar_proximo_ciclo(inicio_ciclo, total_interacoes)


if __name__ == "__main__":
    main()
