import time

import keyboard
import serial
import serial.tools.list_ports
import win32api
import win32con
import win32gui

from utils import teclado_util


class ArduinoMacro:
    def __init__(self, handle):
        self.handle = handle
        self.arduino = None  # Inicializa a variável para o Arduino
        self.q_count = 0
        self.w_count = 0
        self.verificacao_botao_direito_ativa = True
        # self.conectar_arduino()
        self.registrar_teclas()
        self.executar_macro()
        print('---Macro iniciado!')

    def conectar_arduino(self):
        print('---Iniciando conexão com o Arduino...')
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            if 'Arduino' in p.description or 'USB-SERIAL' in p.description or 'Serial USB' in p.description or 'Leonardo' in p.description:
                try:
                    self.arduino = serial.Serial(p.device, baudrate=115200, timeout=.1)
                    break
                except:
                    pass

        time.sleep(3)

        if self.arduino:
            print('---Arduino conectado!')
        else:
            print('---Arduino não conectado!')
            exit()

    def toggle_verificacao(self, event):
        self.verificacao_botao_direito_ativa = not self.verificacao_botao_direito_ativa
        status = "ATIVADO" if self.verificacao_botao_direito_ativa else "DESATIVADO"
        print(f"Botão direito - {status}")

    def registrar_teclas(self):
        keyboard.on_press_key('r', self.toggle_verificacao)

    def executar_macro(self):

        Q = '0x51'
        W = '0x57'
        E = '0x45'
        while True:
            if self.verificacao_botao_direito_ativa:
                if win32api.GetAsyncKeyState(win32con.VK_RBUTTON) < 0:
                    # self.arduino.write(b'999')  # Envia '999' para o Arduino se o botão estiver pressionado
                    self.press_key(self.handle, Q)
                    time.sleep(0.5)
                    self.press_key(self.handle, W)
                    time.sleep(0.5)

                    self.press_key(self.handle, Q)
                    time.sleep(0.5)
                    self.press_key(self.handle, W)
                    time.sleep(0.5)

            time.sleep(0.015)

    #
    # Keyboard.press(156);
    # delay(75);
    # Keyboard.release(156);
    # delay(23);
    #
    # Keyboard.press(162);
    # delay(75);
    # Keyboard.release(162);
    # delay(23);

    def press_key(self, handle, key_code):

        handles_filhos = []
        # Enumera as janelas-filhas da janela principal
        win32gui.EnumChildWindows(handle, self.enum_child_windows_callback, handles_filhos)
        # 459772 -

        # for h in handles_filhos:

        # Simula o pressionamento da tecla (WM_KEYDOWN)
        #     win32gui.SendMessage(h, win32con.WM_CHAR, ord('w'), 0)
        #     win32gui.PostMessage(h, win32con.WM_KEYDOWN, 'W', 0)
        #     time.sleep(0.1)  # Pausa para simular o tempo de pressionamento
        #     # # Simula a liberação da tecla (WM_KEYUP)
        #     win32gui.PostMessage(h, win32con.WM_KEYUP, 'W', 0)

    def enum_child_windows_callback(self, handle, lista_de_handles):
        lista_de_handles.append(handle)
