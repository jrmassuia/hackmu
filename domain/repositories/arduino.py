import time

import pyautogui
import serial
import serial.tools.list_ports
import win32gui

# Constantes para comandos
MENU_CLICK_MOUSE_ESQUERDO = '1'
MENU_ZOOM = '2'
MENU_ENTER = '3'


class Arduino:
    _instancia = None

    def __new__(cls, *args, **kwargs):
        if not cls._instancia:
            cls._instancia = super(Arduino, cls).__new__(cls, *args, **kwargs)
            cls._instancia._inicializar()
        return cls._instancia

    def _inicializar(self):
        self.conexao_arduino = None
        self.conectar()

    def conectar(self):
        if self.conexao_arduino is not None and self.conexao_arduino.is_open:
            print('---Conexão com Arduino já está aberta!')
            return

        print('---Iniciando conexão com o Arduino...')
        conexao = None
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            if 'Arduino' in p.description or 'USB-SERIAL' in p.description or 'Serial USB' in p.description or 'Leonardo' in p.description:
                try:
                    conexao = serial.Serial(p.device, baudrate=115200, timeout=.1)
                    break
                except serial.SerialException as e:
                    print(f'---Erro ao conectar ao Arduino: {e}')

        time.sleep(3)

        if conexao:
            self.conexao_arduino = conexao
            print('---Arduino conectado!')
        else:
            print('---Arduino não conectado!')

    def desconectar(self):
        if self.conexao_arduino and self.conexao_arduino.is_open:
            self.conexao_arduino.close()
            print('---Conexão com Arduino fechada.')

    def comunicar_com_arduino(self, opcao, tempo=.5):
        if self.conexao_arduino:
            self.conexao_arduino.write(bytes(opcao, 'utf-8'))
            time.sleep(tempo)
            self.conexao_arduino.flush()
        else:
            print('---Não está conectado ao Arduino.')

    def enviar_mensagem_arduino(self, mensagem):
        if self.conexao_arduino:
            self.conexao_arduino.write(mensagem.encode('utf-8'))
            self.conexao_arduino.flush()
        else:
            print('---Não está conectado ao Arduino.')

    def verifica_se_eh_arduino_leonardo(self):
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            if 'Leonardo' in p.description:
                return True
        return False

    def enviar_comando(self, handle, comando):
        rect = win32gui.GetWindowRect(handle)
        x_center = (rect[0] + rect[2]) // 2
        y_center = (rect[1] + rect[3]) // 2
        pyautogui.moveTo(x_center, y_center - 30)
        self.executar_click_esquerdo()  # clica na tela
        self.executar_click_esquerdo()  # faz o foco
        self.enviar_mensagem_arduino(comando)

        if comando == MENU_ZOOM:
            time.sleep(2)

        pyautogui.moveTo(10, 10)

    def executar_click_esquerdo(self):
        self.comunicar_com_arduino(MENU_CLICK_MOUSE_ESQUERDO)

    def executar_click_esquerdo_rapido(self):
        self.comunicar_com_arduino(MENU_CLICK_MOUSE_ESQUERDO, tempo=.15)

    def zoom(self, handle):
        self.enviar_comando(handle, MENU_ZOOM)

    def enter(self):
        self.comunicar_com_arduino(MENU_ENTER)
