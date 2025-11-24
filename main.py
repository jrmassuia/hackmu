import threading
import time

from interface_adapters.controller.autopick_controller import AutopickController
from interface_adapters.controller.buf_controller import BufController
from interface_adapters.controller.limpa_pk_controller import LimpaPkController
from interface_adapters.controller.refinar_gem_controler import RefinarGemstoneController
from interface_adapters.controller.refinar_peq_controller import RefinarPequenaController
from interface_adapters.controller.sd_media_controler import SdMediaController
from interface_adapters.controller.sd_small_controller import SdSmallController
from interface_adapters.helpers.session_manager import *
from interface_adapters.pk.controller.pk_controller import PKController
from interface_adapters.recrutar.controller.recrutar_controller import RecrutarController
from interface_adapters.up.controller.up_controller import UpController
from interface_adapters.up.use_case.pick_kanturu_use_case import PickKanturuUseCase
from menu import Menu
from services.foco_mutex_service import FocoMutexService
from sessao_menu import atualizar_menu, obter_menu
from utils.teclado_util import Teclado_util


class MainApp:

    def __init__(self):
        self.menu_autopick = None
        self.telas = []
        self.threads_ativas = []

    def configurar_menu(self):
        for tela, opcoes in self.menu_autopick.items():

            handle_list = self._obter_handles_por_titulo(tela)
            if len(handle_list) == 0:
                tela = tela.replace("/3] MUCABRASIL", "/2] MUCABRASIL")
                handle_list = self._obter_handles_por_titulo(tela)

            if len(handle_list) == 0:
                continue

            handle = handle_list[0]
            ativo = False

            # 🔥 registra o menu dessa tela na seção global
            atualizar_menu(handle, opcoes.copy())

            # controla as telas ativas
            if opcoes.get(Menu.ATIVO, 0) == 1:
                self.telas.append(handle)
                ativo = True

            if ativo:
                self._inicializar_managers(handle)

    def _inicializar_managers(self, handle):
        FocoMutexService().inativar_foco()
        Teclado_util(handle).pressionar_zoon()

    def _obter_handles_por_titulo(self, titulo_parcial):
        handles = []
        win32gui.EnumWindows(
            lambda handle, _: handles.append(handle) if titulo_parcial.lower() in win32gui.GetWindowText(
                handle).lower() else None, None)
        return handles

    def _executar_autopick(self, handle):
        print('Inciando telas:')
        print('--' + win32gui.GetWindowText(handle))
        self.rodar_em_thread(handle, Menu.AUTOPICK)
        time.sleep(2)

    def rodar_em_thread(self, handle, menu):
        obj = None
        if menu == Menu.AUTOPICK:
            obj = AutopickController(handle)
        elif menu == Menu.UPAR:
            obj = UpController(handle)
        elif menu == Menu.BUF:
            obj = BufController(handle)
        elif menu == Menu.REF_PEQ:
            obj = RefinarPequenaController(handle)
        elif menu == Menu.SD_MEDIA:
            obj = SdMediaController(handle)
        elif menu == Menu.LIMPAPK:
            obj = LimpaPkController(handle)
        elif menu == Menu.PICKKANTURU:
            obj = PickKanturuUseCase(handle)
        elif menu == Menu.PKLIZAR:
            obj = PKController(handle)
        elif menu == Menu.RECRUTAR:
            obj = RecrutarController(handle)

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
            sessao = obter_menu(handle)

            if not sessao:
                self._executar_autopick(handle)
                continue

            actions = {
                Menu.UPAR: self._executar_upar,
                Menu.REF_GEM: self._executar_refinar_gem,
                Menu.REF_PEQ: self._executar_refinar_stone,
                Menu.SD_MEDIA: self._executar_sd_media,
                Menu.SD_SMALL: self._executar_sd_small,
                Menu.BUF: self._executar_buf,
                Menu.LIMPAPK: self._executar_limpa_pk,
                Menu.PICKKANTURU: self._executar_pick_kanturu,
                Menu.PKLIZAR: self._executar_pklizar,
                Menu.RECRUTAR: self._executar_recrutar,
            }

            # Procura a primeira opção ativa (== 1) e executa
            for key, action in actions.items():
                if sessao.get(key) == 1:
                    action(handle)
                    break
            else:
                # Nenhuma opção marcada → executa autopick
                self._executar_autopick(handle)

    def _executar_pick_kanturu(self, handle):
        print('Inciando telas:')
        print('--' + win32gui.GetWindowText(handle))
        self.rodar_em_thread(handle, Menu.PICKKANTURU)
        time.sleep(2)

    def _executar_limpa_pk(self, handle):
        print('Inciando telas:')
        print('--' + win32gui.GetWindowText(handle))
        self.rodar_em_thread(handle, Menu.LIMPAPK)
        time.sleep(2)

    def _executar_buf(self, handle):
        print('Inciando telas:')
        print('--' + win32gui.GetWindowText(handle))
        self.rodar_em_thread(handle, Menu.BUF)
        time.sleep(2)

    def _executar_sd_small(self, handle):
        SdSmallController(handle)

    def _executar_sd_media(self, handle):
        print('Inciando telas:')
        print('--' + win32gui.GetWindowText(handle))
        self.rodar_em_thread(handle, Menu.SD_MEDIA)
        time.sleep(2)

    def _executar_refinar_gem(self, handle):
        RefinarGemstoneController(handle)

    def _executar_refinar_stone(self, handle):
        print('Inciando telas:')
        print('--' + win32gui.GetWindowText(handle))
        self.rodar_em_thread(handle, Menu.REF_PEQ)
        time.sleep(2)

    def _executar_upar(self, handle):
        print('Inciando telas:')
        print('--' + win32gui.GetWindowText(handle))
        self.rodar_em_thread(handle, Menu.UPAR)
        time.sleep(2)

    def _executar_pklizar(self, handle):
        print('Inciando telas:')
        print('--' + win32gui.GetWindowText(handle))
        self.rodar_em_thread(handle, Menu.PKLIZAR)
        time.sleep(2)

    def _executar_recrutar(self, handle):
        print('Inciando telas:')
        print('--' + win32gui.GetWindowText(handle))
        self.rodar_em_thread(handle, Menu.RECRUTAR)
        time.sleep(2)

    def finalizar_autopick(self):
        exit()

    def iniciar(self):
        menu_gui = Menu(self)
        menu_gui.run()


if __name__ == "__main__":
    # data_limite = datetime(2025, 10, 30)
    # data_atual = datetime.now()
    # if data_atual > data_limite:
    #
    #     exit()

    # Remove todos os arquivos json

    # Inicializa a aplicação
    app = MainApp()
    app.iniciar()
    app.configurar_menu()
    app.executar_opcao_menu()

    try:
        while True:
            app.monitorar_threads()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Execução interrompida.")
        app.parar_todas_as_threads()
