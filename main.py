import threading
import time

from domain.arduino_teclado import Arduino
from interface_adapters.controller.autopick_controller import AutopickController
from interface_adapters.controller.buf_controller import BufController
from interface_adapters.controller.limpa_pk_controller import LimpaPkController
from interface_adapters.controller.macro_controller import ArduinoMacro
from interface_adapters.controller.refinar_gem_controler import RefinarGemstoneController
from interface_adapters.controller.refinar_peq_controller import RefinarPequenaController
from interface_adapters.controller.sd_media_controler import SdMediaController
from interface_adapters.controller.sd_small_controller import SdSmallController
from interface_adapters.helpers.session_manager import *
from interface_adapters.helpers.session_manager_new import *
from interface_adapters.pk.controller.pk_controller import PKController
from interface_adapters.up.controller.up_controller import UpController
from interface_adapters.up.use_case.pick_kanturu_use_case import PickKanturuUseCase
from menu2 import MenuGUI
from services.foco_mutex_service import FocoMutexService
from utils import encontrar_handle_util, mouse_util
from utils.pointer_util import Pointers
from utils.teclado_util import Teclado_util


class MainApp:
    def __init__(self):
        self.conexao_arduino = Arduino()

        self.menu_geral = None
        self.menu_autopick = None
        self.sessao = None
        self.telas = []
        self.threads_ativas = []

    def configurar_sessao(self):
        for tela, opcoes in self.menu_autopick.items():
            handle = self._obter_handles_por_titulo(tela)
            if len(handle) == 0:
                tela = tela.replace("/3] MUCABRASIL", "/2] MUCABRASIL")
                handle = self._obter_handles_por_titulo(tela)
            ativo = False
            if len(handle) > 0:
                handle = handle[0]
                self.sessao = Sessao(handle=handle)
                for opcao, valor in opcoes.items():
                    self.sessao.atualizar_menu(opcao, valor)
                    if opcao == 'ativo' and valor == 1:
                        self.telas.append(handle)
                        ativo = True
                if ativo:
                    self._inicializar_managers(handle)

    def _inicializar_managers(self, handle):
        self.sessao.atualizar_generico(GenericoFields.HANDLEDIALOGO,
                                       encontrar_handle_util.encontrar_handle_dialgo(handle))

        sessao = Sessao(handle=handle)
        if sessao.ler_menu(MenuFields.LIMPAPK) == 1:
            return

        self.sessao.atualizar_generico(GenericoFields.CLASSE_PERSONAGEM, self._verifica_classe_personagem(handle))
        self.sessao.atualizar_bau(BauFields.BAU_ATUAL, "bau 1")
        self.sessao.atualizar_autopick(AutopickFields.INICIOU_AUTOPICK, "NAO")
        self.sessao.atualizar_inventario(InventarioFields.DATA_HORA_ORGANIZA_COMPLEX, datetime.now().isoformat())
        self.sessao.atualizar_inventario(InventarioFields.DATA_HORA_LIMPAR_INVENTARIO, datetime.now().isoformat())
        self.sessao.atualizar_inventario(InventarioFields.DATA_HORA_GUARDOU_ITEM_NO_BAU, datetime.now().isoformat())
        self.sessao.atualizar_inventario(InventarioFields.VISUALIZAR, "NAO")
        FocoMutexService().inativar_foco()

        Teclado_util(handle, self.conexao_arduino).pressionar_zoon()

    def _verifica_classe_personagem(self, handle):
        classes_por_nome = {
            'MG': ['TOROUVC', 'Vampiro', 'Energumeno'],
            'DL': ['DL_DoMall', 'Narukami', 'BlacK_WinG', 'Omale_DL', 'ReiDav1', 'LAZLU', '_Offensive', 'DL_JirayA'],
            'SM': ['SisteMatyc', 'INFECTRIX', 'BLEKALT_SM', 'CaFeTaoO'],
            'EF': ['Layna_', '_Striper_', 'omale_ME'],
            'BK': ['PitterPark', 'Omale_BK', 'BLEKALTINO']
        }

        pointers = Pointers(handle)
        nome_char = pointers.get_nome_char()

        for classe, nomes in classes_por_nome.items():
            if any(nome in nome_char for nome in nomes):
                return classe

        print('NÃO ACHOU O CHAR ADICIONE AO MAIN: ' + nome_char)

        skills = {
            "SM": [
                "Energy Ball", "Fire Ball", "Power Wave", "Lightning", "Teleport",
                "Meteorite", "Ice", "Poison", "Twister", "Evil Spirit", "Hellfire",
                "Aqua Beam", "Cometfall", "Inferno", "Teleport Ally", "Soul Barrier",
                "Decay", "Nova", "Ice Storm"
            ],
            "BK": [
                "Slash", "Uppercut", "Cyclone", "Lunge", "Twisting Slash",
                "Death Stab", "Greater Fortitude", "Rageful Blow", "Impale",
                "Crescent Moon Slash"
            ],
            "EF": [
                "Heal", "Greater Defense", "Greater Damage", "Triple Shot",
                "Penetration", "Ice Arrow", "Multi-Shot",
                "Summon Goblin", "Summon Stone Golem", "Summon Assassin",
                "Summon Elite Yeti", "Summon Dark Knight", "Summon Bali",
                "Summon Soldier", "Starfall"
            ],
            "MG": [
                "Power Slash", "Flame Strike", "Fire Slash", "Twisting Slash",
                "Death Stab", "Inferno", "Evil Spirit", "Hellfire", "Cometfall",
                "Fire Ball", "Power Wave", "Lightning", "Teleport", "Meteorite",
                "Ice", "Poison", "Twister", "Aqua Beam", "Cometfall", "Inferno",
                "Decay", "Nova", "Ice Storm", "Spiral Slash"
            ],
            "DL": [
                "Force", "Force Wave", "Fire Burst", "Earthquake", "Summon", "Critical Damage",
                "Electric Spark", "Fire Scream"
            ]
        }

        mouse_util.mover(handle, 400, 578)
        time.sleep(.5)

        magia = pointers.get_magia()

        for personagem, magias in skills.items():
            if magia in magias:
                return personagem
        print('Nao achou a magia: ' + magia)

    def _obter_handles_por_titulo(self, titulo_parcial):
        handles = []
        win32gui.EnumWindows(
            lambda handle, _: handles.append(handle) if titulo_parcial.lower() in win32gui.GetWindowText(
                handle).lower() else None, None)
        return handles

    def _executar_autopick(self, handle):
        print('Inciando telas:')
        print('--' + win32gui.GetWindowText(handle))
        self.rodar_em_thread(handle, MenuFields.AUTOPICK)
        time.sleep(2)

    def rodar_em_thread(self, handle, tipoHack):
        obj = None
        if tipoHack == MenuFields.AUTOPICK:
            obj = AutopickController(handle, self.conexao_arduino)
        elif tipoHack == MenuFields.UPAR:
            obj = UpController(handle, self.conexao_arduino)
        elif tipoHack == MenuFields.BUF:
            obj = BufController(handle, self.conexao_arduino)
        elif tipoHack == MenuFields.REF_PEQ:
            obj = RefinarPequenaController(handle, self.conexao_arduino)
        elif tipoHack == MenuFields.SD_MEDIA:
            obj = SdMediaController(handle)
        elif tipoHack == MenuFields.LIMPAPK:
            obj = LimpaPkController(handle)
        elif tipoHack == MenuFields.PICKKANTURU:
            obj = PickKanturuUseCase(handle, self.conexao_arduino)
        elif tipoHack == MenuFields.PKLIZAR:
            obj = PKController(handle, self.conexao_arduino)

        thread = threading.Thread(target=obj.execute)
        self.threads_ativas.append((obj, thread))  # Armazena o objeto e a thread
        thread.start()
        return obj, thread

    def monitorar_threads(self):
        # Monitora as threads e remove as que já terminaram
        for obj, thread in self.threads_ativas[:]:
            if not thread.is_alive():
                print(f"Thread da tela {obj.handle} foi finalizada.")
                self.threads_ativas.remove((obj, thread))

    def parar_todas_as_threads(self):
        # Para todas as threads ativas e aguarda que terminem
        print("Parando todas as execuções")
        for obj, thread in self.threads_ativas:
            obj.parar()  # Para o loop dentro de cada thread
        for obj, thread in self.threads_ativas:
            thread.join()  # Aguarda a thread terminar

    def executar_opcao_menu(self):

        for handle in self.telas:
            sessao = Sessao(handle=handle)

            if sessao.ler_menu(MenuFields.UPAR) == 1:
                self._executar_upar(handle)
            elif sessao.ler_menu(MenuFields.REF_GEM) == 1:
                self._executar_refinar_gem(handle)
            elif sessao.ler_menu(MenuFields.REF_PEQ) == 1:
                self._executar_refinar_stone(handle)
            elif sessao.ler_menu(MenuFields.SD_MEDIA) == 1:
                self._executar_sd_media(handle)
            elif sessao.ler_menu(MenuFields.SD_SMALL) == 1:
                self._executar_sd_small(handle)
            elif sessao.ler_menu(MenuFields.BUF) == 1:
                self._executar_buf(handle)
            elif sessao.ler_menu(MenuFields.LIMPAPK) == 1:
                self._executar_limpa_pk(handle)
            elif sessao.ler_menu(MenuFields.PICKKANTURU) == 1:
                self._executar_pick_kanturu(handle)
            elif sessao.ler_menu(MenuFields.PKLIZAR) == 1:
                self._executar_pklizar(handle)
            else:
                self._executar_autopick(handle)

    def _executar_pick_kanturu(self, handle):
        print('Inciando telas:')
        print('--' + win32gui.GetWindowText(handle))
        self.rodar_em_thread(handle, MenuFields.PICKKANTURU)
        time.sleep(2)

    def _executar_limpa_pk(self, handle):
        print('Inciando telas:')
        print('--' + win32gui.GetWindowText(handle))
        self.rodar_em_thread(handle, MenuFields.LIMPAPK)
        time.sleep(2)

    def _executar_buf(self, handle):
        print('Inciando telas:')
        print('--' + win32gui.GetWindowText(handle))
        self.rodar_em_thread(handle, MenuFields.BUF)
        time.sleep(2)

    def _executar_sd_small(self, handle):
        SdSmallController(handle, self.conexao_arduino)

    def _executar_sd_media(self, handle):
        print('Inciando telas:')
        print('--' + win32gui.GetWindowText(handle))
        self.rodar_em_thread(handle, MenuFields.SD_MEDIA)
        time.sleep(2)

    def _executar_refinar_gem(self, handle):
        RefinarGemstoneController(handle, self.conexao_arduino)

    def _executar_refinar_stone(self, handle):
        print('Inciando telas:')
        print('--' + win32gui.GetWindowText(handle))
        self.rodar_em_thread(handle, MenuFields.REF_PEQ)
        time.sleep(2)

    def _executar_upar(self, handle):
        print('Inciando telas:')
        print('--' + win32gui.GetWindowText(handle))
        self.rodar_em_thread(handle, MenuFields.UPAR)
        time.sleep(2)

    def _executar_pklizar(self, handle):
        print('Inciando telas:')
        print('--' + win32gui.GetWindowText(handle))
        self.rodar_em_thread(handle, MenuFields.PKLIZAR)
        time.sleep(2)

    def _executar_macro(self):
        ArduinoMacro(self.telas[0])

    def finalizar_autopick(self):
        exit()

    def iniciar(self):
        menu_gui = MenuGUI(self)
        menu_gui.run()


if __name__ == "__main__":
    # data_limite = datetime(2025, 10, 30)
    # data_atual = datetime.now()
    # if data_atual > data_limite:
    #
    #     exit()

    # Remove todos os arquivos json
    Sessao.limpar_sessao()

    # Inicializa a aplicação
    app = MainApp()
    app.iniciar()
    app.configurar_sessao()
    app.executar_opcao_menu()

    try:
        while True:
            app.monitorar_threads()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Execução interrompida.")
        app.parar_todas_as_threads()
