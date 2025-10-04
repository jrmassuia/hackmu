import ctypes
import os
import time

import win32api
import win32con
import win32gui

from utils import mouse_util, screenshot_util, limpar_mob_ao_redor_util
from utils.buscar_item_util import BuscarItemUtil
from utils.teclado_util import Teclado_util

usuario32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


class Up_util:

    def __init__(self, handle, pointer=None, conexao_arduino=None):
        self.handle = handle
        self.pointer = pointer
        self.arduino = conexao_arduino
        self.teclado_util = Teclado_util(self.handle, self.arduino)

    def acao_painel_personagem(self, tecla, abrir=True):
        while True:
            self.teclado_util.tap_tecla(tecla)
            time.sleep(.5)
            achou = BuscarItemUtil(self.handle).buscar_posicoes_de_item('./static/img/fechar_painel.png')
            if (abrir and achou) or (abrir is False and achou is None):
                break

    def imagens_sao_iguais(self, img1, img2):
        return screenshot_util.is_image_in_region(img1, img2)

    def selecionar_char_no_launcher(self):
        folder_path = "./static/up/char"
        mouse_util.tira_mouse_tela(self.handle)
        while True:
            for filename in os.listdir(folder_path):
                if filename.endswith((".png", ".jpg")):
                    image_position = self.verifica_se_personagem_esta_na_tela(folder_path, filename)
                    if image_position:
                        x, y = image_position
                        mouse_util.left_clique(self.handle, x, y + 155)
                        mouse_util.left_clique(self.handle, x, y + 155)
                        time.sleep(1)
                        self.clicar_na_imagem_ou_fallback('./static/img/btnconnect.png', None)
                        time.sleep(5)

                        image_position = self.verifica_se_personagem_esta_na_tela(folder_path, filename)
                        if image_position:
                            print('Não achou personagem ao selecionar no launcher: ' + filename)
                            self.selecionar_char_no_launcher()
                        else:
                            print('Achou personagem ao selecionar no launcher: ' + filename)
                            self.teclado_util.selecionar_skill_1()
                            self.teclado_util.pressionar_zoon()
                            return True

    def verifica_se_personagem_esta_na_tela(self, folder_path, filename):
        template_image_path = os.path.join(folder_path, filename)
        screenshot = screenshot_util.capture_window(self.handle)
        image_position = BuscarItemUtil(self.handle).buscar_imagem_na_janela(screenshot,
                                                                             template_image_path,
                                                                             precisao=.80)
        return image_position

    def clicar_na_imagem_ou_fallback(self, imagem_path, fallback_position, timeout=60):
        mouse_util.mover(self.handle, 1, 1)
        start_time = time.time()
        while time.time() - start_time < timeout:
            posicao = BuscarItemUtil(self.handle).buscar_item_simples(imagem_path)
            if posicao:
                mouse_util.left_clique(self.handle, posicao[0], posicao[1])
                return True
            else:
                if fallback_position:
                    mouse_util.mover_click(*fallback_position)
        return False

    def ativar_up_e_centralizar(self):
        mouse_util.ativar_click_direito(self.handle)
        mouse_util.moverCentro(self.handle)

    def ativar_up(self):
        mouse_util.ativar_click_direito(self.handle)

    def desativar_up(self):
        mouse_util.desativar_click_direito(self.handle)

    def clicar_bau(self, x, y):
        if self.arduino.conexao_arduino:
            with self.teclado_util.foco_mutex.focar_mutex():
                self.teclado_util.focus_window()
                self.teclado_util.pressionar_tecla('LALT')
                mouse_util.left_clique(self.handle, x, y)
                self.teclado_util.soltar_tecla('LALT')
        else:
            mouse_util.left_clique(self.handle, x, y)

    def limpar_mob_ao_redor(self, tempo_inicial_limpar_mob_ao_redor, classe):
        if tempo_inicial_limpar_mob_ao_redor is None:
            tempo_inicial_limpar_mob_ao_redor = 999999
        if (time.time() - tempo_inicial_limpar_mob_ao_redor) > 600:
            tempo_inicial_limpar_mob_ao_redor = time.time()
            limpar_mob_ao_redor_util.limpar_mob_ao_redor(self.handle)
            if self.pointer.get_ponto_lvl() > 0:
                if classe == 'DL':
                    if self.pointer.get_reset() >= 250:
                        add = "/v"
                    else:
                        add = "/e"
                elif classe == 'EF':
                    if self.pointer.get_reset() >= 200:
                        add = "/v"
                    else:
                        add = "/a"
                else:
                    add = "/a"

                self.teclado_util.escrever_texto(add + " " + str(self.pointer.get_ponto_lvl()))
        return tempo_inicial_limpar_mob_ao_redor

    def ativar_skill(self, classe, tempo_inicial_ativar_skill):
        if tempo_inicial_ativar_skill == 0 or ((time.time() - tempo_inicial_ativar_skill) > 600):  # 10 mtos
            tempo_inicial_ativar_skill = time.time()
            if classe == 'EF':
                self.teclado_util.selecionar_skill_2()
                mouse_util.clickDireito(self.handle)
                self.teclado_util.selecionar_skill_3()
                mouse_util.clickDireito(self.handle)
                self.teclado_util.selecionar_skill_1()
            elif classe == 'DL':
                self.teclado_util.selecionar_skill_2()
                mouse_util.clickDireito(self.handle)
                self.teclado_util.selecionar_skill_1()
        return tempo_inicial_ativar_skill

    def ativar_desc_item_spot(self):
        if self.pointer.get_mostrar_desc_item() == 0:
            self.teclado_util.tap_alt()

    def enviar_comandos_iniciais(self):
        self.teclado_util.escrever_texto(["/re off", "/autopick on", "/autodc off"])
        self.teclado_util.pressionar_zoon()

    def paniel_lateral_esta_aberto(self):
        return self.pointer.get_painel_lateral_aberto_item() == 1

    def focar_janela(self, handle: int, pausa_final: float = 0.05) -> bool:
        """
        Traz a janela indicada por `handle` para frente e define o foco de forma robusta.
        Retorna True se obteve sucesso.
        """
        try:
            if not handle or not win32gui.IsWindow(handle):
                return False

            # Usa a janela raiz/top-level (evita child windows)
            GA_ROOT = 2
            raiz = usuario32.GetAncestor(handle, GA_ROOT) or handle
            handle = raiz

            # Se estiver minimizada, restaura
            if win32gui.IsIconic(handle):
                win32gui.ShowWindow(handle, win32con.SW_RESTORE)
                time.sleep(0.05)
            else:
                win32gui.ShowWindow(handle, win32con.SW_SHOW)

            # Threads para liberar foco (só se necessário)
            id_thread_atual = kernel32.GetCurrentThreadId()
            janela_frontal = usuario32.GetForegroundWindow()
            thread_frontal = usuario32.GetWindowThreadProcessId(janela_frontal, 0) if janela_frontal else 0
            thread_destino = usuario32.GetWindowThreadProcessId(handle, 0)

            anexou_fg = anexou_dst = False
            if thread_frontal and thread_frontal != id_thread_atual:
                if usuario32.AttachThreadInput(id_thread_atual, thread_frontal, True):
                    anexou_fg = True
            if thread_destino and thread_destino != id_thread_atual:
                if usuario32.AttachThreadInput(id_thread_atual, thread_destino, True):
                    anexou_dst = True

            # Gera um input mínimo de usuário (ajuda a burlar ForegroundLockTimeout)
            win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
            time.sleep(0.01)
            win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)

            # Pulso TOPMOST para ajustar Z-order
            win32gui.SetWindowPos(handle, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
            time.sleep(0.01)
            win32gui.SetWindowPos(handle, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)

            ok_top = usuario32.BringWindowToTop(handle)
            ok_setfg = usuario32.SetForegroundWindow(handle)
            ok_focus = usuario32.SetFocus(handle) != 0

            if not (ok_setfg and ok_focus):
                # Fallbacks que ajudam em alguns apps/jogos
                usuario32.SetActiveWindow(handle)
                win32gui.SetWindowPos(handle, win32con.HWND_TOP, 0, 0, 0, 0,
                                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
                time.sleep(0.01)
                ok_setfg = usuario32.SetForegroundWindow(handle) or ok_setfg
                ok_focus = (usuario32.SetFocus(handle) != 0) or ok_focus

            sucesso = bool(ok_top and ok_setfg and ok_focus)

        finally:
            # Desatacha se anexou
            if 'anexou_fg' in locals() and anexou_fg:
                usuario32.AttachThreadInput(id_thread_atual, thread_frontal, False)
            if 'anexou_dst' in locals() and anexou_dst:
                usuario32.AttachThreadInput(id_thread_atual, thread_destino, False)

        time.sleep(pausa_final)
        return sucesso

################################################################
# def acao_painel_personagem(handle, tecla, abrir=True):
#     while True:
#         teclado_util.pressionar_tecla_foco(handle, tecla)
#         time.sleep(.5)
#         achou = BuscarItemUtil(handle).buscar_posicoes_de_item('./static/img/fechar_painel.png')
#         if (abrir and achou) or (abrir is False and achou is None):
#             break


# def imagens_sao_iguais(img1, img2):
#     return screenshot_util.is_image_in_region(img1, img2)

#
# def selecionar_char_no_launcher(handle):
#     folder_path = "./static/up/char"
#     mouse_util.tira_mouse_tela(handle)
#     while True:
#         for filename in os.listdir(folder_path):
#             if filename.endswith((".png", ".jpg")):
#                 image_position = verifica_se_personagem_esta_na_tela(handle, folder_path, filename)
#                 if image_position:
#                     x, y = image_position
#                     mouse_util.left_clique(handle, x, y + 150)
#                     mouse_util.left_clique(handle, x, y + 150)
#                     time.sleep(1)
#                     clicar_na_imagem_ou_fallback(handle, './static/img/btnconnect.png', None)
#                     time.sleep(5)
#
#                     image_position = verifica_se_personagem_esta_na_tela(handle, folder_path, filename)
#                     if image_position:
#                         print('Não achou personagem ao selecionar no launcher: ' + filename)
#                         selecionar_char_no_launcher(handle)
#                     else:
#                         print('Achou personagem ao selecionar no launcher: ' + filename)
#                         teclado_util.pressionar_tecla_foco(handle, teclado_util.VK_1)
#                         teclado_util.pressionar_zoon(handle)
#                         return True


# def verifica_se_personagem_esta_na_tela(handle, folder_path, filename):
#     template_image_path = os.path.join(folder_path, filename)
#     screenshot = screenshot_util.capture_window(handle)
#     # image_position = find_image_in_window(screenshot, template_image_path, confidence_threshold=.80)
#     image_position = BuscarItemUtil(handle).buscar_imagem_na_janela(screenshot,
#                                                                     template_image_path,
#                                                                     precisao=.70)
#     return image_position


# def clicar_na_imagem_ou_fallback(handle, imagem_path, fallback_position, timeout=60):
#     mouse_util.mover(handle, 1, 1)
#     start_time = time.time()
#     while time.time() - start_time < timeout:
#         posicao = BuscarItemUtil(handle).buscar_item_simples(imagem_path)
#         if posicao:
#             mouse_util.left_clique(handle, posicao[0], posicao[1])
#             return True
#         else:
#             if fallback_position:
#                 mouse_util.mover_click(*fallback_position)
#     return False


# def ativar_up_e_centralizar(handle):
#     mouse_util.ativar_click_direito(handle)
#     mouse_util.moverCentro(handle)


# def ativar_up(handle):
#     mouse_util.ativar_click_direito(handle)
#
#
# def desativar_up(handle):
#     mouse_util.desativar_click_direito(handle)


# def clicar_bau(handle, x, y):
#     teclado_util.focus_window(handle)
#     interception.auto_capture_devices()
#     with interception.hold_key("alt"):
#         mouse_util.left_clique(handle, x, y)
#         time.sleep(0.02)


# def limpar_mob_ao_redor(handle, tempo_inicial_limpar_mob_ao_redor, pointer, classe):
#     if tempo_inicial_limpar_mob_ao_redor is None:
#         tempo_inicial_limpar_mob_ao_redor = 999999
#     if (time.time() - tempo_inicial_limpar_mob_ao_redor) > 600:
#         tempo_inicial_limpar_mob_ao_redor = time.time()
#         limpar_mob_ao_redor_util.limpar_mob_ao_redor(handle)
#         if pointer.get_ponto_lvl() > 0:
#             if classe == 'DL':
#                 if pointer.get_reset() >= 250:
#                     add = "/v"
#                 else:
#                     add = "/e"
#             else:
#                 add = "/a"
#
#             teclado_util.escrever_texto_foco(handle, add + " " + str(pointer.get_ponto_lvl()))
#     return tempo_inicial_limpar_mob_ao_redor


# def ativar_skill(handle, classe, tempo_inicial_ativar_skill):
#     if tempo_inicial_ativar_skill == 0 or ((time.time() - tempo_inicial_ativar_skill) > 600):  # 10 mtos
#         tempo_inicial_ativar_skill = time.time()
#         if classe == 'EF':
#             teclado_util.selecionar_skill_2(handle)
#             mouse_util.right_clique(handle, 400, 255, delay=.5)
#             teclado_util.selecionar_skill_3(handle)
#             mouse_util.right_clique(handle, 400, 255, delay=.5)
#             teclado_util.selecionar_skill_1(handle)
#         elif classe == 'DL':
#             teclado_util.selecionar_skill_2(handle)
#             mouse_util.right_clique(handle, 400, 255, delay=.5)
#             teclado_util.selecionar_skill_1(handle)
#     return tempo_inicial_ativar_skill


# def ativar_desc_item_spot(handle, pointer):
#     if pointer.get_mostrar_desc_item() == 0:
#         teclado_util.pressionar_alt_foco(handle)

#
# def enviar_comandos_iniciais(handle):
#     teclado_util.escrever_texto_foco(handle, ["/re off", "/autopick on", "/autodc off"])
#     teclado_util.pressionar_zoon(handle)


# def paniel_lateral_esta_aberto(pointer):
#     return pointer.get_painel_lateral_aberto_item() == 1
