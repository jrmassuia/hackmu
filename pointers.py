import math
import re
import ctypes
import psutil
import pygetwindow as gw
import pymem


class Pointers:
    def __init__(self, pid):
        self.pm = pymem.Pymem()
        self.pm.open_process_from_id(pid)
        self.CLIENT = self.pm.base_address

        self.PROCESS_NAME = "mucabrasil.exe"  # Nome do processo do jogo
        self.MODULE_NAME = "mucabrasil.exe"  # Nome do módulo do jogo
        self.BASE_OFFSETS = [0x00000000, 0x00000000]  # Dois endereços base mapeados
        self.OFFSETS_CADEIA_HP = [0x00]
        self.OFFSETS_CADEIA_SD = [0x00]

        self.DC_POINTER = 0x012CE35C
        self.CHAR_NAME_POINTER = 0x011450EC
        self.LEVEL_POINTER = self.get_pointer(self.CLIENT + 0x00D450EC, offsets=[0x3C4])
        self.HP_POINTER = self.get_pointer(self.CLIENT + 0x00D450EC, offsets=[0x3B8])
        self.HP_PLUS_POINTER = self.get_pointer(self.CLIENT + 0x00D450EC, offsets=[0xE4])
        self.HP_BUFF_POINTER = self.get_pointer(self.CLIENT + 0x00D450EC, offsets=[0xE0])
        self.MAX_HP_POINTER = self.get_pointer(self.CLIENT + 0x00D450EC, offsets=[0xDC])

        self.MANA_POINTER = self.get_pointer(self.CLIENT + 0x00D450EC, offsets=[0x3BC])
        self.MANA_BUFF_POINTER = self.get_pointer(self.CLIENT + 0x00D450EC, offsets=[0x6F0])
        self.MAX_MANA_POINTER = self.get_pointer(self.CLIENT + 0x00D450EC, offsets=[0x6EC])

        self.X_POINTER = self.get_pointer(self.CLIENT + 0x00D450EC, offsets=[0x810])
        self.Y_POINTER = self.get_pointer(self.CLIENT + 0x00D450EC, offsets=[0x814])

        self.BATTLE_STATUS_POINTER = self.get_pointer(self.CLIENT + 0x00D450EC, offsets=[0x854])
        self.SIT_POINTER = self.get_pointer(self.CLIENT + 0x00D450EC, offsets=[0x290])

        self.TARGET_HP_POINTER = self.get_pointer(0x012CE2E0, offsets=[0x18, 0x59C, 0x0, 0xC, 0x1F4, 0x15C, 0x480])
        self.TARGET_SELECT = self.get_pointer(self.CLIENT + 0x00EC05C8, offsets=[0xD0, 0x2DC, 0x24, 0xC10])
        self.TARGET_NAME_POINTER = self.get_pointer(0x012CE2E0, offsets=[0x18, 0xB1C, 0x0, 0xC, 0x1F8, 0x43C])

        self.TEAM_SIZE_POINTER = self.get_pointer(0x0106D328, offsets=[0x3D8])
        self.TEAM_NAME_1 = self.get_pointer(0x012CE2E0, offsets=[0x18, 0x77C, 0x0, 0xC, 0x678, 0x8B4])
        self.TEAM_NAME_2 = self.get_pointer(0x012CE2E0, offsets=[0x18, 0x34C, 0x0, 0xC, 0x678, 0x8B4])
        self.TEAM_NAME_3 = self.get_pointer(0x012CE2E0, offsets=[0x18, 0x3F4, 0x0, 0xC, 0x1F4, 0x15C])
        self.TEAM_NAME_4 = self.get_pointer(0x012CE2E0, offsets=[0x18, 0xA1C, 0x0, 0xC, 0x1F4, 0x54])

        self.BAG_OPEN_POINTER = self.get_pointer(0x012CE2E0, offsets=[0x18, 0x5C4, 0x0, 0xC, 0x1F8, 0x42C, 0xBA0])
        #print("Pointers initialized.", pid)

        self.mapear()



    def get_pointer(self, base_address, offsets):
        """
        Calcula o ponteiro final seguindo uma cadeia de offsets.
        """
        try:
            address = base_address
            for offset in offsets:  # Navega pelos offsets até o endereço final
                address = self.pm.read_int(address) + offset
            return address
        except Exception as e:
            #print(f"Erro ao calcular o ponteiro: {e}")
            return None

    def read_value(self, address, data_type="byte"):
        try:
            if data_type == "byte":
                return self.pm.read_bytes(address, 1)[0]  # Lê 1 byte
            elif data_type == "int":
                return self.pm.read_int(address)  # Lê 4 bytes como inteiro
            elif data_type == "float":
                return self.pm.read_float(address)  # Lê 4 bytes como float
            else:
                print(f"Tipo de dado desconhecido: {data_type}")
                return None
        except Exception as e:
            print(f"Erro ao ler valor ({data_type}): {e}")
            return None

    def read_string_from_pointer(self, base_pointer, offset=0, max_length=50):
        try:
            pointer_address = self.pm.read_int(base_pointer)
            final_address = pointer_address + offset
            byte_data = self.pm.read_bytes(final_address, max_length)
            string_data = byte_data.split(b'\x00', 1)[0].decode('utf-8', errors='ignore')
            return string_data
        except Exception as e:
            print(f"String Error: {e}")
            return "Offline Account"

    def get_char_name(self):
        name = self.read_string_from_pointer(self.CHAR_NAME_POINTER, offset=0xBC, max_length=50)

        if re.match(r"^[\w]+$", name):  # Alfanumérico
            return name

        # Segunda tentativa
        pointer = self.get_pointer(self.CLIENT + 0x00D450EC, offsets=[0xBC])
        if pointer:
            name = self.read_string_from_pointer(pointer, offset=0x0, max_length=50)
        return name

    def get_target_name(self):
        return self.read_string_from_pointer(self.TARGET_NAME_POINTER, offset=0x9AC, max_length=50)
            
    def team_name_1(self):
        name = self.read_string_from_pointer(self.TEAM_NAME_1, offset=0x4F4, max_length=50)

        if re.match(r"^[\w]+$", name):  # Alfanumérico
            return name
        pointer = self.get_pointer(0x012CE2E0, offsets=[0x18, 0x77C, 0x0, 0xC, 0x678, 0x8B4, 0x4F4])
        if pointer:
            name = self.read_string_from_pointer(pointer, offset=0x0, max_length=50)
        return name

    def team_name_2(self):
        name = self.read_string_from_pointer(self.TEAM_NAME_2, offset=0x4F4, max_length=50)
        if re.match(r"^[\w]+$", name):
            return name
        pointer = self.get_pointer(0x012CE2E0, offsets=[0x18, 0x34C, 0x0, 0xC, 0x678, 0x8B4, 0x4F4])
        if pointer:
            name = self.read_string_from_pointer(pointer, offset=0x0, max_length=50)
        return name

    def team_name_3(self):
        name = self.read_string_from_pointer(self.TEAM_NAME_3, offset=0x54, max_length=50)
        if re.match(r"^[\w]+$", name):
            return name
        pointer = self.get_pointer(0x012CE2E0, offsets=[0x18, 0x3F4, 0x0, 0xC, 0x1F4, 0x15C, 0x54])
        if pointer:
            name = self.read_string_from_pointer(pointer, offset=0x0, max_length=50)
        return name

    def team_name_4(self):
        name = self.read_string_from_pointer(self.TEAM_NAME_4, offset=0x54, max_length=50)
        if re.match(r"^[\w]+$", name):
            return name
        pointer = self.get_pointer(0x012CE2E0, offsets=[0x18, 0xA1C, 0x0, 0xC, 0x1F4, 0x54, 0x54])
        if pointer:
            name = self.read_string_from_pointer(pointer, offset=0x0, max_length=50)
        return name

    def get_level(self):
        return self.read_value(self.LEVEL_POINTER, data_type="byte")

    def is_target_selected(self):
        if self.TARGET_SELECT is None:
            print("Erro: Ponteiro TARGET_SELECT não calculado.")
            return False

        target = self.read_value(self.TARGET_SELECT, data_type="byte")  # Lê 1 byte
        if target == 1:
            #print("Target selected")
            return True
        return False

    def target_hp(self):
        hp = self.read_value(self.TARGET_HP_POINTER, data_type="int")
        return hp

    def target_hp_full(self):
        return self.read_value(self.TARGET_HP_POINTER, data_type="int") == 597

    def is_target_dead(self):
        dead = self.read_value(self.TARGET_HP_POINTER, data_type="int")
        if dead == 0:
            return True

    def get_hp(self):
        return self.read_value(self.HP_POINTER, data_type="int")

    def get_hp_plus(self):
        plus = self.read_value(self.HP_PLUS_POINTER, data_type="byte")
        # if plus >= 100:
        #     return plus - 100
        # else:
        #     return plus

    def get_hp_buff(self):
        return self.read_value(self.HP_BUFF_POINTER, data_type="int")

    def get_max_hp(self):
        base_hp = self.read_value(self.MAX_HP_POINTER, data_type="int")
        buff_hp = self.get_hp_buff()
        # hp_total = base_hp + buff_hp
        # plus = self.get_hp_plus()
        #
        # if plus == 1:
        #     print("IGUAL 1")
        #     return base_hp
        # else:
        #     return math.floor(((hp_total * plus) / 100) + hp_total)

    def get_mana(self):
        return self.read_value(self.MANA_POINTER, data_type="int")

    def get_mana_buff(self):
        return self.read_value(self.MANA_BUFF_POINTER, data_type="int")

    def get_max_mana(self):
        base_mana = self.read_value(self.MAX_MANA_POINTER, data_type="int")
        buff_mana = self.get_mana_buff()
        mana_total = base_mana + buff_mana
        return mana_total

    def is_in_battle(self):
        battle = self.read_value(self.BATTLE_STATUS_POINTER, data_type="byte")
        if battle == 1:
            #print("Battle Status")
            return True

    def is_sitting(self):
        sitting = self.read_value(self.SIT_POINTER, data_type="byte")
        if sitting == 200:
            return True
        else:
            return False

    def get_x(self):
        x = self.read_value(self.X_POINTER, data_type="float") / 20
        return x > 0 and math.floor(x) or math.ceil(x)

    def get_y(self):
        y = self.read_value(self.Y_POINTER, data_type="float") / 20
        return y > 0 and math.floor(y) or math.ceil(y)

    def is_bag_open(self):
        bag = self.read_value(self.BAG_OPEN_POINTER, data_type="int")
        if bag == 903:
            return True

    def get_team_size(self):
        team = self.read_value(self.TEAM_SIZE_POINTER, data_type="int")
        if team is None:
            return 0
        else:
            return team

    def get_dc(self):
        dc = self.read_value(self.DC_POINTER, data_type="int")
        return dc

    def mapear(self, pm):

        global hp_address, sd_address, hp_max_address, sd_max_address

        try:
            # Obtendo o módulo base
            for module in pm.list_modules():
                if module.name.lower() == self.MODULE_NAME:
                    module_base = module.lpBaseOfDll
                    print(f"[INFO] Módulo Base ({self.MODULE_NAME}) encontrado: {hex(module_base)}")
                    break
            else:
                print("[ERRO] Módulo não encontrado.")
                return None

            # Tentando ambos os endereços base para HP e SD
            for base_offset in self.BASE_OFFSETS:
                endereco_atual_hp = module_base + base_offset
                endereco_atual_sd = module_base + base_offset

                try:
                    # Mapeando o HP e HP Máximo
                    for offset in self.OFFSETS_CADEIA_HP:
                        endereco_atual_hp = pm.read_int(endereco_atual_hp)
                        if endereco_atual_hp == 0:
                            break
                        endereco_atual_hp += offset

                    # Mapeando o SD e SD Máximo
                    for offset in self.OFFSETS_CADEIA_SD:
                        endereco_atual_sd = pm.read_int(endereco_atual_sd)
                        if endereco_atual_sd == 0:
                            break
                        endereco_atual_sd += offset

                    # Endereços de HP e SD Máximo (relativo)
                    hp_max_address = endereco_atual_hp + 0x8
                    sd_max_address = endereco_atual_sd + 0x4

                    # Verificando se os dois foram encontrados
                    if endereco_atual_hp and endereco_atual_sd:
                        hp_address = endereco_atual_hp
                        sd_address = endereco_atual_sd
                        return hp_address, sd_address, hp_max_address, sd_max_address

                except:
                    continue

            print("[ERRO] Nenhum endereço base válido encontrado.")
            return None, None, None, None

        except Exception as e:
            print(f"[ERRO] Falha ao mapear os endereços do HP e SD: {e}")
            return None, None,None,None


def get_pid_from_hwnd(hwnd):
    pid = ctypes.c_ulong()
    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def find_pid_by_window_title(window_title):
    # Obtém todas as janelas abertas
    windows = gw.getAllTitles()

    # Procura a janela pelo título
    for title in windows:
        if window_title.lower() in title.lower():
            # Obtém a janela correspondente
            window = gw.getWindowsWithTitle(title)[0]
            # Obtém o handle da janela
            hwnd = window._hWnd

            # Obtém o PID usando o handle
            pid = get_pid_from_hwnd(hwnd)
            return pid

    return None

def find_process_pid():
    process_name = "mucabrasil.exe"
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'].lower() == process_name.lower():
            return proc.info['pid']
    return None

# Exemplo de uso
window_title = "[1/3] MUCABRASIL"
pid = find_pid_by_window_title(window_title)
p = Pointers(pid)

if p.is_target_selected():
    print("Um alvo está selecionado!")
else:
    print("Nenhum alvo está selecionado.")

name = p.get_char_name()
print(f"CHAR_NAME: {name}")
level = p.get_level()
print(f"LEVEL: {level}")
team_name_1 = p.team_name_1()
print(f"TEAM_NAME_1: {team_name_1}")
team_name_2 = p.team_name_2()
print(f"TEAM_NAME_2: {team_name_2}")
team_name_3 = p.team_name_3()
print(f"TEAM_NAME_3: {team_name_3}")
team_name_4 = p.team_name_4()
print(f"TEAM_NAME_4: {team_name_4}")
hp = p.target_hp()
print(f"TARGET_HP: {hp}")
target_name = p.get_target_name()
print(f"TARGET_NAME: {target_name}")
get_hp = p.get_hp()
print(f"CHAR_HP : {get_hp}")
hp_plus = p.get_hp_plus()
print(f"CHAR_HP_PLUS : {hp_plus}")
hp_buff = p.get_hp_buff()
print(f"CHAR_HP_BUFF : {hp_buff}")
max_hp = p.get_max_hp()
print(f"CHAR_MAX_HP : {max_hp}")
battle = p.is_in_battle()
print(f"CHAR_BATTLE_STATUS : {battle}")
mana = p.get_mana()
print(f"CHAR_MANA : {mana}")
mana_buff = p.get_mana_buff()
# print(f"CHAR_MANA_BUFF : {mana_buff}")
# max_mana = p.get_max_mana()
# print(f"CHAR_MAX_MANA : {max_mana}")
sit = p.is_sitting()
print(f"CHAR_SIT : {sit}")
x_pos = p.get_x()
print(f"CHAR_X_POS : {x_pos}")
y_pos = p.get_y()
print(f"CHAR_Y_POS : {y_pos}")
bag_open = p.is_bag_open()
print(f"CHAR_BAG_OPEN : {bag_open}")
team_size = p.get_team_size()
print(f"TEAM_SIZE : {team_size}")
dc = p.get_dc()
print(f"CHAR_DC : {dc}")
