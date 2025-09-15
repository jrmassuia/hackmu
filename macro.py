import serial
import serial.tools.list_ports
import win32api
import win32con
import time
import keyboard
import win32gui

from utils.RegionColorDetector import RegionColorDetector

# Configura a comunicação serial rrrrrrrrrrrcom o Arduino
arduino = None  # Inicializa a variável para o Arduino

# regiao = (100, 579, 2, 2)
regiao = (183, 935, 2, 2)
colors = [(130, 52, 9),
          (134, 54, 11),
          (184, 73, 13),
          (193, 77, 16)]


# colors = [(195, 80, 15),
#           (239, 116, 13)]


def conectarArduino():
    print('---Iniciando conexão com o Arduino...')
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if 'Arduino' in p.description or 'USB-SERIAL' in p.description or 'Serial USB' in p.description or 'Leonardo' in p.description:
            try:
                arduino = serial.Serial(p.device, baudrate=115200, timeout=.1)
                break
            except:
                pass

    time.sleep(3)

    if arduino:
        print('---Arduino conectado!')
    else:
        print('---Arduino não conectado!')
        exit()
    return arduino


# Inicializar os contadores
q_count = 0
w_count = 0

# Variável para controlar se a verificação do botão direito está ativa
verificacao_botao_direito_ativa = True


# Função que será chamada quando a teclarr Q for pressionada
def count_q(event):
    global q_count
    q_count += 1


# Função que será chamada quando a tecla W for pressionada
def count_w(event):
    global w_count
    w_count += 1


# Função para alternar a verificação do botão direito com a tecla 'r'
def toggle_verificacao(event):
    global verificacao_botao_direito_ativa
    verificacao_botao_direito_ativa = not verificacao_botao_direito_ativa
    status = "ATIVADO" if verificacao_botao_direito_ativa else "DESATIVADO"
    print(f"{status} - Botão direito")


# Registrar as funções para as teclas Q, W e V
keyboard.on_press_key('r', toggle_verificacao)  # Ativar/desativar a vvverificação do botão direito

# Conectar ao Arduinovvvvr
if arduino is None:
    arduino = conectarArduino()
    print('---Macro iniciado!')


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

while True:
    # Verifica se a verificação do botão direito está ativa
    if verificacao_botao_direito_ativa:

        # Verifica se o botão direito do mouse está pressionado
        if win32api.GetKeyState(win32con.VK_RBUTTON) < 0:
            detector = RegionColorDetector(handle, regiao, colors)
            resultado = detector.detect_colors()
            if resultado:
                arduino.write('888'.encode('utf-8'))
            else:
                arduino.write('999'.encode('utf-8'))

    time.sleep(0.015)
