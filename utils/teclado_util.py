import ctypes
import time
from typing import Iterable

import pyautogui
import win32con
import win32gui

from domain.arduino_teclado import Arduino
from services.foco_mutex_service import FocoMutexService
from sessao_handle import get_handle_atual

kernel32 = ctypes.windll.kernel32
usuario32 = ctypes.windll.user32

TENTATIVAS_PADRAO = 10


class Teclado_util:

    def __init__(self):
        self.handle = get_handle_atual()
        self.arduino = Arduino()
        self.foco_mutex = FocoMutexService()

    def focus_window(self):
        pyautogui.FAILSAFE = False
        pyautogui.press("alt")
        win32gui.SetForegroundWindow(self.handle)
        time.sleep(.05)

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
        else:
            print('erro')

    def selecionar_skill_2(self):
        if self.arduino.conexao_arduino:
            self.tap_tecla('2')

    def selecionar_skill_3(self):
        if self.arduino.conexao_arduino:
            self.tap_tecla('3')

    def selecionar_skill_4(self):
        if self.arduino.conexao_arduino:
            self.tap_tecla('4')

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

    def combo_tecla(self, *keys: str):
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

    def _combo_arduino(self, *keys: str) -> None:
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

    def digitar_token(self, senha):
        janelas = self._listar_janelas_filhas()
        if len(janelas) < 1:
            return
        self._enviar_texto_por_handle(janelas[-1], senha)

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
