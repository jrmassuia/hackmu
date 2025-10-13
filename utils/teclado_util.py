import ctypes
import time
from typing import Iterable

import win32con
import win32gui

from services.foco_mutex_service import FocoMutexService

kernel32 = ctypes.windll.kernel32
usuario32 = ctypes.windll.user32

TENTATIVAS_PADRAO = 10


class Teclado_util:

    def __init__(self, handle, arduino):
        self.handle = handle
        self.arduino = arduino
        self.foco_mutex = FocoMutexService()

    def focus_window(self):
        if win32gui.IsIconic(self.handle):
            win32gui.ShowWindow(self.handle, win32con.SW_RESTORE)

        id_thread_atual = kernel32.GetCurrentThreadId()
        janela_frontal = usuario32.GetForegroundWindow()
        thread_frontal = usuario32.GetWindowThreadProcessId(janela_frontal, 0) if janela_frontal else 0
        thread_destino = usuario32.GetWindowThreadProcessId(self.handle, 0)

        usuario32.AttachThreadInput(id_thread_atual, thread_frontal, True)
        usuario32.AttachThreadInput(id_thread_atual, thread_destino, True)
        try:
            usuario32.SetForegroundWindow(self.handle)
            usuario32.SetFocus(self.handle)
            usuario32.BringWindowToTop(self.handle)
        finally:
            usuario32.AttachThreadInput(id_thread_atual, thread_frontal, False)
            usuario32.AttachThreadInput(id_thread_atual, thread_destino, False)

        self._pausa(0.05)

    def tap_enter(self):
        if self.arduino.conexao_arduino:
            self.tap_tecla('ENTER')

    def tap_espaco(self):
        if self.arduino.conexao_arduino:
            self.tap_tecla('SPACE')

    def tap_alt(self):
        if self.arduino.conexao_arduino:
            self.tap_tecla('LALT')

    def tap_esc(self):
        if self.arduino.conexao_arduino:
            self.tap_tecla('ESC')

    def selecionar_skill_1(self):
        if self.arduino.conexao_arduino:
            self.tap_tecla('1')

    def selecionar_skill_2(self):
        if self.arduino.conexao_arduino:
            self.tap_tecla('2')

    def selecionar_skill_3(self):
        if self.arduino.conexao_arduino:
            self.tap_tecla('3')

    def pressionar_zoon(self):
        if self.arduino.conexao_arduino:
            with self.foco_mutex.focar_mutex():
                self.focus_window()
                self.arduino.tap('NUM-')
                self.arduino.tap('NUM-')
                self.arduino.tap('NUM-')
                self.arduino.tap('NUM-')

    def pressionar_tecla(self, tecla):
        if self.arduino.conexao_arduino:
            self.arduino.down(tecla)

    def soltar_tecla(self, tecla):
        if self.arduino.conexao_arduino:
            self.arduino.up(tecla)

    def tap_tecla(self, tecla):
        tentativas = TENTATIVAS_PADRAO
        for tentativa in range(tentativas):
            with self.foco_mutex.focar_mutex():
                try:
                    if self.arduino.conexao_arduino:
                        self.focus_window()
                        self._toque_arduino(tecla)
                    break
                except Exception as e:
                    print(f"[Tentativa {tentativa + 1}] Erro ao enviar tecla: {e}")
                    self._pausa(0.5)
        else:
            print("Falha ao enviar tecla após múltiplas tentativas.")

    def combo_tecla(self,  *keys: str):
        tentativas = TENTATIVAS_PADRAO
        for tentativa in range(tentativas):
            with self.foco_mutex.focar_mutex():
                try:
                    if self.arduino.conexao_arduino:
                        self.focus_window()
                        self._combo_arduino(*keys)
                    break
                except Exception as e:
                    print(f"[Tentativa {tentativa + 1}] Erro ao enviar tecla: {e}")
                    self._pausa(0.5)
        else:
            print("Falha ao enviar tecla após múltiplas tentativas.")

    def escrever_texto(self, text, enviar_por_cx_texto=True):
        if self.arduino.conexao_arduino:
            tentativas = TENTATIVAS_PADRAO
            for tentativa in range(tentativas):
                with self.foco_mutex.focar_mutex():
                    try:
                        self.focus_window()

                        # Normaliza para lista de comandos
                        if isinstance(text, str):
                            comandos: Iterable[str] = [text]
                        elif isinstance(text, (list, tuple)):
                            comandos = list(text)
                        else:
                            comandos = [str(text)]

                        for cmd in comandos:
                            if enviar_por_cx_texto:
                                self._toque_arduino('ENTER')
                                self._pausa(0.025)
                            self._digitar_texto_arduino(cmd)
                            if enviar_por_cx_texto:
                                self._toque_arduino('ENTER')
                                self._pausa(0.025)
                        break
                    except Exception as e:
                        print(f"[Tentativa {tentativa + 1}] Erro ao enviar texto: {e}")
                        self._pausa(0.5)
            else:
                print("Falha ao enviar texto após múltiplas tentativas.")


    def _toque_arduino(self, tecla: str, delay=0.025) -> None:
        if self.arduino.conexao_arduino:
            self.arduino.tap(tecla, delay=delay)

    def _combo_arduino(self,  *keys: str) -> None:
        if self.arduino.conexao_arduino:
            self.arduino.combo(*keys)

    def _digitar_texto_arduino(self, texto: str) -> None:
        if self.arduino.conexao_arduino:
            self.arduino.type_text(texto)

    def _pausa(self, segundos: float) -> None:
        time.sleep(segundos)

    def digitar_texto_email(self, textoPara, textoTitulo, textoCorpo):
        janelas = self._listar_janelas_filhas()
        if len(janelas) < 3:
            return
        self._enviar_texto_por_handle(janelas[-3], textoPara)  # Para
        self._enviar_texto_por_handle(janelas[-2], textoTitulo)  # Título
        self._enviar_texto_por_handle(janelas[-1], textoCorpo)  # Corpo

    def digitar_senha(self, senha):
        janelas = self._listar_janelas_filhas()
        if len(janelas) < 2:
            return
        self._enviar_texto_por_handle(janelas[-2], senha)

    def _listar_janelas_filhas(self):
        janelas: list[int] = []
        win32gui.EnumChildWindows(self.handle, self.enum_child_windows_callback, janelas)
        return janelas

    def enum_child_windows_callback(self, handle, lista_de_handles):
        lista_de_handles.append(handle)

    def _enviar_texto_por_handle(self, handle, texto: str, pausa_caractere: float = 0.01) -> None:
        for caractere in texto:
            win32gui.SendMessage(handle, win32con.WM_CHAR, ord(caractere), 0)
            # self._pausa(pausa_caractere)

################################################################################################

# @contextmanager
# def _foco_mutex():
#     foco = FocoMutexService()
#     foco.ativar_foco()
#     try:
#         yield
#     finally:
#         foco.inativar_foco()


# def focus_window(hwnd):
#     if win32gui.IsIconic(hwnd):
#         win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
#
#     id_thread_atual = kernel32.GetCurrentThreadId()
#     janela_frontal = usuario32.GetForegroundWindow()
#     thread_frontal = usuario32.GetWindowThreadProcessId(janela_frontal, 0) if janela_frontal else 0
#     thread_destino = usuario32.GetWindowThreadProcessId(hwnd, 0)
#
#     usuario32.AttachThreadInput(id_thread_atual, thread_frontal, True)
#     usuario32.AttachThreadInput(id_thread_atual, thread_destino, True)
#     try:
#         usuario32.SetForegroundWindow(hwnd)
#         usuario32.SetFocus(hwnd)
#         usuario32.BringWindowToTop(hwnd)
#     finally:
#         usuario32.AttachThreadInput(id_thread_atual, thread_frontal, False)
#         usuario32.AttachThreadInput(id_thread_atual, thread_destino, False)
#
#     _pausa(0.05)


# def _pausa(segundos: float) -> None:
#     time.sleep(segundos)


# def pressionar_esc(handle):
#     with _foco_mutex():
#         focus_window(handle)
#         pressionar_tecla("esc")


# def pressionar_zoon(handle):
#     with _foco_mutex():
#         focus_window(handle)
#         pressionar_tecla("subtract")
#         pressionar_tecla("subtract")
#         pressionar_tecla("subtract")


# def pressionar_enter():
#     pressionar_tecla("enter")

#
# def pressionar_espaco_foco(handle):
#     pressionar_tecla_foco(handle, "space")
#
#
# def pressionar_alt_foco(handle):
#     pressionar_tecla_foco(handle, "alt")
#
#
# def selecionar_skill_1(handle):
#     pressionar_tecla_foco(handle, "1")
#
#
# def selecionar_skill_2(handle):
#     pressionar_tecla_foco(handle, "2")
#
#
# def selecionar_skill_3(handle):
#     pressionar_tecla_foco(handle, "3")


# def escrever_texto_foco(handle, text):
#     for tentativa in range(TENTATIVAS_PADRAO):
#         with _foco_mutex():
#             try:
#                 sessao = Sessao(handle=handle)
#                 handle_dialogo = sessao.ler_generico(GenericoFields.HANDLEDIALOGO)
#                 focus_window(handle)
#
#                 if isinstance(text, str):
#                     comandos: Iterable[str] = [text]
#                 elif isinstance(text, (list, tuple)):
#                     comandos = list(text)
#                 else:
#                     comandos = [str(text)]
#
#                 for cmd in comandos:
#                     pressionar_enter()  # abre chat
#                     _pausa(0.1)
#                     _enviar_caracteres(handle_dialogo, cmd, pausa_caractere=0.02)
#                     pressionar_enter()  # fecha chat
#                     _pausa(0.1)
#                 break
#             except Exception as e:
#                 print(f"[Tentativa {tentativa + 1}] Erro ao enviar texto: {e}")
#                 _pausa(0.5)
#
#     else:
#         print("Falha ao enviar texto após múltiplas tentativas.")


# def enviar_texto_email(handle, textoPara, textoTitulo, textoCorpo):
#     janelas = _listar_janelas_filhas(handle)
#     if len(janelas) < 3:
#         return
#     escrever_texto(janelas[-3], textoPara)  # Para
#     escrever_texto(janelas[-2], textoTitulo)  # Título
#     escrever_texto(janelas[-1], textoCorpo)  # Corpo


# def enviar_texto_senha(handle, senha):
#     janelas = _listar_janelas_filhas(handle)
#     if len(janelas) < 2:
#         return
#     escrever_texto(janelas[-2], senha)


# def _listar_janelas_filhas(handle: int) -> list[int]:
#     janelas: list[int] = []
#     win32gui.EnumChildWindows(handle, enum_child_windows_callback, janelas)
#     return janelas


# def enum_child_windows_callback(handle, lista_de_handles):
#     lista_de_handles.append(handle)
#
#
# def escrever_texto(handle, texto):
#     _enviar_caracteres(handle, texto, pausa_caractere=0.0)
#
#
# def _enviar_caracteres(handle: int, texto: str, pausa_caractere: float = 0.01) -> None:
#     for caractere in texto:
#         win32gui.SendMessage(handle, win32con.WM_CHAR, ord(caractere), 0)
#         _pausa(pausa_caractere)


# def pressionar_tecla(tecla: str, delay=0.1) -> None:
#     interception.auto_capture_devices()
#     with interception.hold_key(tecla):
#         time.sleep(delay)


# def pressionar_tecla_foco(handle, tecla: str):
#     for tentativa in range(TENTATIVAS_PADRAO):
#         with _foco_mutex():
#             try:
#                 focus_window(handle)
#                 pressionar_tecla(tecla)
#                 break  # sucesso
#             except Exception as e:
#                 print(f"[Tentativa {tentativa + 1}] Erro ao enviar tecla: {e}")
#                 _pausa(0.5)
#     else:
#         print("Falha ao enviar tecla após múltiplas tentativas.")
