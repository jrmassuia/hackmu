import time

import serial
import serial.tools.list_ports

# -------------------- COMANDOS EXISTENTES (compatibilidade) --------------------
MENU_CLICK_MOUSE_ESQUERDO = '1'
MENU_ZOOM = '2'
MENU_ENTER = '3'

# -------------------- NOVO: MAPA DE TECLAS (sem numpad) --------------------
# Use nomes exatamente como abaixo. São os mesmos reconhecidos pelo sketch do Arduino.
KEYS_VALIDOS = {
    # topo
    "ESC","F1","F2","F3","F4","F5","F6","F7","F8","F9","F10","F11","F12",
    # fileira números (linha superior)
    "GRAVE","1","2","3","4","5","6","7","8","9","0","MINUS","EQUAL","BACKSPACE",
    # tab -> backslash
    "TAB","Q","W","E","R","T","Y","U","I","O","P","LBRACKET","RBRACKET","BACKSLASH",
    # caps -> enter
    "CAPSLOCK","A","S","D","F","G","H","J","K","L","SEMICOLON","QUOTE","ENTER",
    # shift -> rshift
    "LSHIFT","Z","X","C","V","B","N","M","COMMA","DOT","SLASH","RSHIFT",
    # ctrl/gui/alt/space/alt/…
    "LCTRL","LGUI","LALT","SPACE","RALT","RGUI","MENU","RCTRL",
    # navegação
    "INSERT","DELETE","HOME","END","PAGEUP","PAGEDOWN","LEFT","UP","RIGHT","DOWN",
    # NUMPAD
    "NUM0", "NUM1", "NUM2", "NUM3", "NUM4", "NUM5", "NUM6", "NUM7", "NUM8", "NUM9",
    "NUM.", "NUMDOT", "NUM/", "NUMSLASH", "NUM*", "NUMSTAR",
    "NUM-", "NUMMINUS", "NUM+", "NUMPLUS",
    "NUMENTER", "NUMLOCK",
}

# Mapa opcional de VK -> NOME (se você já chama por VK code)
VK_TO_NAME = {
    0x1B: "ESC",
    0x0D: "ENTER",
    0x20: "SPACE",
    0x25: "LEFT", 0x26: "UP", 0x27: "RIGHT", 0x28: "DOWN",
    0x70: "F1", 0x71: "F2", 0x72: "F3", 0x73: "F4",
    0x74: "F5", 0x75: "F6", 0x76: "F7", 0x77: "F8",
    0x78: "F9", 0x79: "F10", 0x7A: "F11", 0x7B: "F12",
    0x08: "BACKSPACE", 0x09: "TAB",
    0x14: "CAPSLOCK",
    0x2D: "INSERT", 0x2E: "DELETE",
    0x24: "HOME", 0x23: "END",
    0x21: "PAGEUP", 0x22: "PAGEDOWN",
    0x10: "LSHIFT", 0x11: "LCTRL", 0x12: "LALT",
    # Dígitos linha superior
    0x30: "0", 0x31: "1", 0x32: "2", 0x33: "3", 0x34: "4",
    0x35: "5", 0x36: "6", 0x37: "7", 0x38: "8", 0x39: "9",
}

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

    # -------------------- CONEXÃO --------------------
    def conectar(self):
        if self.conexao_arduino is not None and self.conexao_arduino.is_open:
            print('---Conexão com Arduino já está aberta!')
            return

        print('---Iniciando conexão com o Arduino...')
        conexao = None
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            if ('Arduino' in p.description
                or 'USB-SERIAL' in p.description
                or 'Serial USB' in p.description
                or 'Leonardo' in p.description):
                try:
                    conexao = serial.Serial(p.device, baudrate=115200, timeout=.1)
                    break
                except serial.SerialException as e:
                    print(f'---Erro ao conectar ao Arduino: {e}')

        # Leonardo costuma resetar ao abrir porta
        time.sleep(2.5)

        if conexao:
            self.conexao_arduino = conexao
            print('---Arduino conectado!')
        else:
            print('---Arduino não conectado!')

    def desconectar(self):
        if self.conexao_arduino and self.conexao_arduino.is_open:
            self.conexao_arduino.close()
            print('---Conexão com Arduino fechada.')

    # -------------------- CAMADA SERIAL (compat antiga + nova) --------------------
    def comunicar_com_arduino(self, opcao, tempo=.5):
        """Compat anterior (manda um byte/char) — mantém para seus cliques/zoom."""
        if self.conexao_arduino:
            self.conexao_arduino.write(bytes(opcao, 'utf-8'))
            time.sleep(tempo)
            self.conexao_arduino.flush()
        else:
            print('---Não está conectado ao Arduino.')

    def enviar_mensagem_arduino(self, mensagem):
        """Nova camada: envia linha com \n (protocolo TAP/TYPE/DOWN/UP/COMBO)."""
        if self.conexao_arduino:
            if not mensagem.endswith('\n'):
                mensagem += '\n'
            # esvazia input para ler um eventual "OK"
            self.conexao_arduino.reset_input_buffer()
            self.conexao_arduino.write(mensagem.encode('utf-8'))
            self.conexao_arduino.flush()
            # ACK simples (opcional)
            deadline = time.time() + 1.5
            buf = b""
            while time.time() < deadline:
                if self.conexao_arduino.in_waiting:
                    buf += self.conexao_arduino.read(self.conexao_arduino.in_waiting)
                    if b"OK" in buf:
                        break
                time.sleep(0.01)
        else:
            print('---Não está conectado ao Arduino.')

    def verifica_se_eh_arduino_leonardo(self):
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            if 'Leonardo' in p.description:
                return True
        return False

    # -------------------- NOVO: TECLADO HID VIA SERIAL --------------------
    def _nome_tecla_de_vk(self, vk_code: int) -> str | None:
        # tenta VK direto
        if vk_code in VK_TO_NAME:
            return VK_TO_NAME[vk_code]
        # tenta caractere imprimível
        try:
            ch = chr(vk_code)
            if ch.isprintable() and len(ch) == 1:
                return ch.upper()
        except Exception:
            pass
        return None

    def tap(self, key_name: str, delay=0.025):
        """Pressiona e solta (TAP:<KEY>)."""
        key = key_name.strip().upper()
        if key not in KEYS_VALIDOS and not (len(key) == 1 and key.isprintable()):
            raise ValueError(f"Tecla '{key_name}' não suportada (sem numpad).")
        self.enviar_mensagem_arduino(f"TAP:{key}")
        time.sleep(delay)

    def tap_vk(self, vk_code: int, delay=0.05):
        """Permite chamar com VK code (0x0D etc.)."""
        name = self._nome_tecla_de_vk(vk_code)
        if not name:
            raise ValueError(f"VK 0x{vk_code:02X} não mapeado.")
        self.tap(name, delay=delay)

    def down(self, key_name: str):
        key = key_name.strip().upper()
        if key not in KEYS_VALIDOS and not (len(key) == 1 and key.isprintable()):
            raise ValueError(f"Tecla '{key_name}' não suportada.")
        self.enviar_mensagem_arduino(f"DOWN:{key}")

    def up(self, key_name: str):
        key = key_name.strip().upper()
        if key not in KEYS_VALIDOS and not (len(key) == 1 and key.isprintable()):
            raise ValueError(f"Tecla '{key_name}' não suportada.")
        self.enviar_mensagem_arduino(f"UP:{key}")

    def type_text(self, texto: str, enter_no_final=False, delay_entre_blocos=0.01):
        """Digita texto (para chat), respeitando layout do SO."""
        # quebra em blocos para não saturar
        CHUNK = 150
        for i in range(0, len(texto), CHUNK):
            trecho = texto[i:i+CHUNK]
            self.enviar_mensagem_arduino(f"TYPE:{trecho}")
            time.sleep(delay_entre_blocos)
        # if enter_no_final:
        #     self.enviar_mensagem_arduino("TAP:ENTER")

    def combo(self, *keys: str):
        """
        Pressiona várias teclas juntas (Ctrl+Shift+S):
        combo("LCTRL", "LSHIFT", "S")
        """
        norm = [k.strip().upper() for k in keys]
        for k in norm:
            if k not in KEYS_VALIDOS and not (len(k) == 1 and k.isprintable()):
                raise ValueError(f"Tecla '{k}' não suportada no combo.")
        self.enviar_mensagem_arduino(f"COMBO:{'+'.join(norm)}")
