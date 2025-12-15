import threading
import time
import win32gui

from domain.arduino_teclado import Arduino
from interface_adapters.controller.autopick_controller import AutopickController
from interface_adapters.controller.buf_controller import BufController
from interface_adapters.controller.limpa_pk_controller import LimpaPkController
from interface_adapters.controller.refinar_gem_controler import RefinarGemstoneController
from interface_adapters.controller.refinar_peq_controller import RefinarPequenaController
from interface_adapters.controller.sd_media_controler import SdMediaController
from interface_adapters.controller.sd_small_controller import SdSmallController
from interface_adapters.pk.controller.pk_controller import PKController
from interface_adapters.recrutar.controller.recrutar_controller import RecrutarController
from interface_adapters.teste.controller.teste_controller import TesteController
from interface_adapters.up.controller.up_controller import UpController
from interface_adapters.up.use_case.pick_kanturu_use_case import PickKanturuUseCase
from menu import Menu
from services.foco_mutex_service import FocoMutexService
from sessao_menu import atualizar_menu, obter_menu


class MainApp:
    THREAD_START_DELAY = 2.0

    # 1) Mapa central: Menu -> Classe que possui .execute() e .parar()
    EXECUTAVEIS = {
        Menu.AUTOPICK: AutopickController,
        Menu.UPAR: UpController,
        Menu.BUF: BufController,
        Menu.REF_PEQ: RefinarPequenaController,
        Menu.REF_GEM: RefinarGemstoneController,
        Menu.SD_MEDIA: SdMediaController,
        Menu.SD_SMALL: SdSmallController,
        Menu.LIMPAPK: LimpaPkController,
        Menu.PICKKANTURU: PickKanturuUseCase,
        Menu.PKLIZAR: PKController,
        Menu.RECRUTAR: RecrutarController,
        Menu.TESTE: TesteController,
    }

    # 2) Ordem de prioridade ao ler o "sessao_menu"
    PRIORIDADE_ACOES = [
        Menu.UPAR,
        Menu.REF_GEM,
        Menu.REF_PEQ,
        Menu.SD_MEDIA,
        Menu.SD_SMALL,
        Menu.BUF,
        Menu.LIMPAPK,
        Menu.PICKKANTURU,
        Menu.PKLIZAR,
        Menu.RECRUTAR,
        Menu.TESTE,
    ]

    def __init__(self):
        self.menu_autopick = None
        self.telas = []
        self.threads_ativas = []  # lista de tuplas (obj, thread)
        self.arduino = Arduino()

        self._aguardar_conexao_arduino(timeout=10.0)
        FocoMutexService().inativar_foco()

    # ----------------------------
    # Setup / utilidades
    # ----------------------------

    def _aguardar_conexao_arduino(self, timeout: float) -> None:
        inicio = time.time()
        while not self.arduino.conexao_arduino and (time.time() - inicio) < timeout:
            time.sleep(0.1)

        if not self.arduino.conexao_arduino:
            print("Não foi possível conectar ao Arduino dentro do tempo limite.")

    def _obter_handles_por_titulo(self, titulo_parcial: str) -> list[int]:
        handles: list[int] = []

        def cb(handle, _):
            titulo = win32gui.GetWindowText(handle).lower()
            if titulo_parcial.lower() in titulo:
                handles.append(handle)

        win32gui.EnumWindows(cb, None)
        return handles

    def _obter_handle(self, titulo: str) -> int | None:
        # tenta /3 e se falhar tenta /2 (seu comportamento original)
        handles = self._obter_handles_por_titulo(titulo)
        if not handles:
            titulo_alt = titulo.replace("/3] MUCABRASIL", "/2] MUCABRASIL")
            handles = self._obter_handles_por_titulo(titulo_alt)
        return handles[0] if handles else None

    def configurar_menu(self):
        for titulo_tela, opcoes in (self.menu_autopick or {}).items():
            handle = self._obter_handle(titulo_tela)
            if not handle:
                continue

            atualizar_menu(handle, opcoes.copy())

            if opcoes.get(Menu.ATIVO, 0) == 1:
                self.telas.append(handle)

    # ----------------------------
    # Execução de ações
    # ----------------------------

    def _log_inicio(self, handle: int):
        print("Iniciando tela:")
        print("--" + win32gui.GetWindowText(handle))

    def _iniciar_acao(self, handle: int, menu: str):
        cls = self.EXECUTAVEIS.get(menu)
        if not cls:
            print(f"[WARN] Menu '{menu}' não mapeado. Caindo no AUTOPICK.")
            cls = self.EXECUTAVEIS[Menu.AUTOPICK]
            menu = Menu.AUTOPICK

        self._log_inicio(handle)

        obj = cls(handle)
        thread = threading.Thread(target=obj.execute, daemon=True)
        self.threads_ativas.append((obj, thread))
        thread.start()

        time.sleep(self.THREAD_START_DELAY)
        return obj, thread

    def executar_opcao_menu(self):
        for handle in self.telas:
            sessao = obter_menu(handle)

            # sem sessão -> autopick
            if not sessao:
                self._iniciar_acao(handle, Menu.AUTOPICK)
                continue

            menu_escolhido = self._primeira_acao_ativa(sessao) or Menu.AUTOPICK
            self._iniciar_acao(handle, menu_escolhido)

    def _primeira_acao_ativa(self, sessao: dict) -> str | None:
        for menu in self.PRIORIDADE_ACOES:
            if sessao.get(menu) == 1:
                return menu
        return None

    # ----------------------------
    # Gerência de threads
    # ----------------------------

    def monitorar_threads(self):
        for obj, thread in self.threads_ativas[:]:
            if not thread.is_alive():
                print(f"Thread da tela {getattr(obj, 'handle', '?')} foi finalizada.")
                self.threads_ativas.remove((obj, thread))

    def parar_todas_as_threads(self):
        print("Parando todas as execuções")
        for obj, _thread in self.threads_ativas:
            if hasattr(obj, "parar"):
                obj.parar()

        for _obj, thread in self.threads_ativas:
            thread.join()

    # ----------------------------
    # App
    # ----------------------------

    def finalizar_autopick(self):
        exit()

    def iniciar(self):
        menu_gui = Menu(self)
        menu_gui.run()


if __name__ == "__main__":
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
