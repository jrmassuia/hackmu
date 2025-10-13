import math
import random
import threading
import time
import win32gui

from abc import ABC, abstractmethod
from typing import Optional, Sequence, Tuple, Callable
from interface_adapters.helpers.session_manager_new import Sessao, GenericoFields
from interface_adapters.up.up_util.up_util import Up_util
from services.alterar_char_sala_service import AlterarCharSalaService
from services.buscar_personagem_proximo_service import BuscarPersoangemProximoService
from services.posicionamento_spot_service import PosicionamentoSpotService
from utils import screenshot_util, mouse_util, spot_util
from utils.buscar_item_util import BuscarItemUtil
from utils.json_file_manager_util import JsonFileManager
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers
from utils.rota_util import PathFinder
from utils.teclado_util import Teclado_util


class PkBase(ABC):
    """Base reutilizável para fluxos de PK. A subclasse define:
       - qual senha/tipo de PK usar (_definir_tipo_pk_e_senha)
       - como iniciar o ciclo de PK (iniciar_pk)
       - como sair da safe, checar morte, corrigir coordenadas e movimentar/posicionar para PK.
    """

    IMG_PK0 = './static/pk/pk0.png'
    IMG_PK1 = './static/pk/pk1.png'
    IMG_OKINFO = './static/pk/okinfo.png'

    # =========================
    #     CICLO DE VIDA
    # =========================
    def __init__(self, handle, arduino, mapa):
        # Contexto / dependências
        self.handle = handle
        self.sessao = Sessao(handle=handle)
        self.pointer = Pointers(handle)
        self.classe = self.sessao.ler_generico(GenericoFields.CLASSE_PERSONAGEM)
        self.tela = win32gui.GetWindowText(handle)
        self.mapa = mapa

        # Utilitários (mantidos)
        self.teclado_util = Teclado_util(self.handle, arduino)
        self.mover_spot_util = MoverSpotUtil(self.handle)
        self.up_util = Up_util(self.handle, pointer=self.pointer, conexao_arduino=arduino)
        self.buscar_personagem = BuscarPersoangemProximoService(self.pointer)
        self.buscar_imagem = BuscarItemUtil(self.handle)

        # Dados auxiliares
        self.arquivo_json = "./data/personagens.json"
        self.json_manager = JsonFileManager(self.arquivo_json)
        self.personagens = self.json_manager.read().get("Personagem", [])

        # Estado de execução
        self.coord_mouse_atual: Optional[Tuple[int, int]] = None
        self.coord_spot_atual: Optional[Tuple[int, int]] = None
        self.tipo_pk: Optional[str] = None
        self._abates = 0
        self._abates_lock = threading.Lock()

        # Define tipo e senha (fornecidos pela subclasse)
        senha = self._definir_tipo_pk_e_senha()

        # Serviço de alternância de sala
        self.alternar_sala = AlterarCharSalaService(handle, senha, arduino)

    # ---------- Métodos de ciclo externo ----------
    def execute(self):
        """Loop principal: lê PK -> se limpo, inicia PK; senão, rotina de limpar PK."""
        while True:
            limpou_pk = self._limpou_pk()
            if limpou_pk is None:
                print("erro leitura pk")
                continue

            if limpou_pk:
                self.iniciar_pk()
                if self.pointer.get_nome_char() != 'Narukami':
                    print('Esperando 60s!')
                    time.sleep(60)
            else:
                self.limpar_pk()

    @abstractmethod
    def _definir_tipo_pk_e_senha(self) -> str:
        """Subclasse define e retorna a senha. Também deve setar self.tipo_pk."""
        raise NotImplementedError()

    @abstractmethod
    def iniciar_pk(self) -> None:
        """Fluxo ao começar PK (sequência de spots conforme o tipo definido)."""
        raise NotImplementedError()

    def executar_rota_pk(self, etapas: Sequence[Callable[[], list]]) -> None:
        """
        Executa, em sequência, cada etapa da rota de PK:
          - chama a função geradora de spots
          - executa PK nesses spots
          - verifica se pode continuar; se não, encerra a rota
        """
        for obter_spots in etapas:
            spots = obter_spots()  # função que retorna os spots
            self._executar_pk(spots)  # executa PK nos spots
            if not self._pk_pode_continuar():  # se não pode continuar, sai
                return

    def _consultar_info_e_verificar(self, imagem_pk: str) -> bool:
        """
        Fluxo comum: mover mouse -> /info -> aguardar -> verificar imagem-alvo (pk0/pk1)
        -> clicar OK -> retornar True/False conforme encontrado.
        Mantém a lógica original, com limpeza de pequenas arestas.
        """
        if self.pointer.get_nome_char() == 'Narukami':
            return True  # early return preservado

        while True:
            mouse_util.mover(self.handle, 1, 1)  # tira o mouse da tela
            self.teclado_util.escrever_texto("/info")
            time.sleep(1)
            achou_btn = self.buscar_imagem.buscar_item_simples(self.IMG_OKINFO)
            if achou_btn:
                break

        achou = self._eh_pk(imagem_pk)
        # Fecha o /info de forma robusta
        self._mover_e_clicar_na_opcao(self.IMG_OKINFO)
        return bool(achou)

    def _limpou_pk(self) -> Optional[bool]:
        return self._consultar_info_e_verificar(self.IMG_PK0)

    def _pk_pode_continuar(self) -> bool:
        return self._consultar_info_e_verificar(self.IMG_PK1) or self._consultar_info_e_verificar(self.IMG_PK0)

    def _eh_pk(self, image_path: str) -> bool:
        screenshot = screenshot_util.capture_region(self.handle, 350, 270, 80, 25)
        return bool(self.buscar_imagem.buscar_posicoes_de_item(image_path, screenshot, precisao=.9))

    def _mover_e_clicar_na_opcao(self, imagem_path: str, timeout: float = 5.0) -> bool:
        """
        Move o mouse, tenta localizar a imagem e clicar nela até *sumir*.
        Corrigido: antes a flag `achou` era zerada a cada iteração.
        Agora: ao encontrar uma vez, passamos a observar o sumiço para confirmar sucesso.
        """
        mouse_util.mover(self.handle, 1, 1)
        start = time.time()
        ja_clicou = False

        while time.time() - start < timeout:
            posicao = self.buscar_imagem.buscar_item_simples(imagem_path)

            if posicao:
                mouse_util.left_clique(self.handle, *posicao)
                ja_clicou = True
                time.sleep(0.15)
                continue

            # Se já clicou e agora não acha mais -> sumiu da tela => sucesso
            if ja_clicou and posicao is None:
                return True

            time.sleep(0.1)

        return False

    # ---------- Rotina de limpar PK ----------
    def limpar_pk(self):
        """
        Rotina para limpar PK:
         - vai para sala 2
         - desativa PK
         - posiciona em spot vazio
         - ativa up e checa PK periodicamente
        """
        self.mover_para_sala2()
        self._desativar_pk()
        self.teclado_util.escrever_texto('/re off')
        self.up_util.ativar_desc_item_spot()
        self.mover_para_spot_vazio()

        ultimo_check_up = time.time()
        ultimo_check_pk = time.time()

        while True:
            # a cada ~0.5s, reativa o UP (mantendo a lógica original, só organizada)
            if time.time() - ultimo_check_up >= 0.5:
                self.up_util.ativar_up()
                ultimo_check_up = time.time()

            if self.morreu():
                tempo_espera = random.randint(3 * 60, 10 * 60)
                print(f"Aguardando {tempo_espera // 60} minutos ({tempo_espera} segundos)... - " + self.tela)
                time.sleep(tempo_espera)
                self.mover_para_spot_vazio()

            # a cada 180s, checa se limpou PK
            if time.time() - ultimo_check_pk >= 180:
                ultimo_check_pk = time.time()
                limpou_pk = self._limpou_pk()
                if limpou_pk:
                    self.mover_para_sala7()
                    return

            self._corrigir_coordenada_e_mouse()

    # ---------- Navegação e posicionamento genéricos ----------
    def mover_para_sala2(self):
        if self.pointer.get_sala_atual() != 2:
            self.alternar_sala.selecionar_sala(2)

    def mover_para_sala7(self):
        if self.pointer.get_sala_atual() != 7:
            self.alternar_sala.selecionar_sala(7)

    def mover_para_spot_vazio(self):
        self.teclado_util.selecionar_skill_1()
        self._sair_da_safe()

        if self.mapa == PathFinder.MAPA_AIDA:
            spots = spot_util.buscar_spots_aida_2()
        elif self.mapa == PathFinder.MAPA_TARKAN:
            spots = spot_util.buscar_spots_todos_tk(nao_ignorar_spot_pk=True)
        else:
            spots = ''

        poscionar = PosicionamentoSpotService(
            self.handle,
            self.pointer,
            self.mover_spot_util,
            self.classe,
            None,
            spots,
            self.mapa
        )

        achou_spot = poscionar.posicionar_bot_up()
        if achou_spot:
            self.coord_mouse_atual = poscionar.get_coord_mouse()
            self.coord_spot_atual = poscionar.get_coord_spot()

    # ---------- Pontos de extensão obrigatórios ----------
    @abstractmethod
    def _corrigir_coordenada_e_mouse(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def morreu(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def _movimentar_char_spot(self, coordenadas: Tuple[int, int]) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def _posicionar_char_pklizar(self, x: int, y: int) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def _sair_da_safe(self) -> None:
        raise NotImplementedError()

    # ---------- Núcleo de caça (comum) ----------
    def _executar_pk(self, spots: Sequence[Sequence[Tuple[Sequence[str], Sequence[Tuple[int, int]], Tuple[int, int]]]]):
        """
        Percorre grupos de spots. Mantém a lógica original, só mais explícita:
        - Move para spot elegível (que contenha 'SM')
        - Lista personagens próximos (filtra self e mobs ignorados)
        - Posiciona para pklizar, verifica suicídio/loja e ativa PK + clique direito
        """
        for indice_spot, grupo_de_spots in enumerate(spots):
            for grupo in grupo_de_spots:
                classes, coordenadas_spot, coordenada_mouse = grupo

                if 'SM' not in classes:
                    continue

                coordenadas = coordenadas_spot[0]
                movimentou = self._movimentar_char_spot(coordenadas)

                if not movimentou:
                    print('1 - Morreu enqto procurava player')
                    return

                resultados = self.buscar_personagem.listar_nomes_e_coords_por_padrao()
                if not resultados:
                    continue

                char_proximos = self.buscar_personagem.ordenar_proximos(resultados, limite=20)

                for d in char_proximos:
                    nome = d.get("nome", "")
                    x = d.get("x", "")
                    y = d.get("y", "")

                    posicionou = self._posicionar_char_pklizar(x, y)

                    if posicionou:
                        self._tentar_pklizar()
                    else:
                        print('NÃO POSICIONOU!')

    # --- helpers ---------------------------------------------------------------

    def _buscar_pk_cascata(self, prioridade: str | None = None, timeout_total: float = 2.0,
                           intervalo: float = 0.10) -> str | None:
        """
        Procura pelas imagens em cascata por até `timeout_total` segundos (TOTAL).
        Se `prioridade` vier, checa ela primeiro em todas as iterações.
        Retorna o caminho da imagem encontrada ou None.
        """
        imagens_pk = (
            './static/pk/loja.png',
            './static/pk/suiciide.png',
            './static/pk/fenix.png',
            './static/pk/suici.png',
            './static/pk/suic.png',
            './static/pk/suicide.png',
            './static/pk/suicide2.png',
        )

        deadline = time.monotonic() + timeout_total
        while time.monotonic() < deadline:
            # 1) tenta a prioritaria primeiro (se houver)
            if prioridade and self.buscar_imagem.buscar_item_simples(prioridade):
                return prioridade

            # 2) varre as demais em cascata
            for img in imagens_pk:
                if img == prioridade:
                    continue
                if self.buscar_imagem.buscar_item_simples(img):
                    return img

            time.sleep(intervalo)

        return None

    def _vigiar_imagem_ate_sumir(self, img_path: str, confirmar_desaparecimento_ms: int = 400,
                                 intervalo: float = 0.08) -> bool:
        """
        Mantém a vigilância da MESMA imagem até ela sumir.
        Usa um 'debounce' de `confirmar_desaparecimento_ms` (faltas consecutivas)
        para evitar falsos negativos por flicker.
        Retorna True quando confirmar que sumiu; False se interrompido (ex.: morreu).
        """
        # quantas faltas consecutivas precisamos para cravar que sumiu
        faltas_necessarias = max(1, math.ceil(confirmar_desaparecimento_ms / (intervalo * 1000)))
        faltas = 0

        timeout_total = 180
        deadline = time.monotonic() + timeout_total
        while time.monotonic() < deadline:
            if self.mover_spot_util.esta_na_safe:
                print('3 - Morreu enquanto vigiava o oponente')
                return False

            self.teclado_util.tap_tecla("Q")

            mouse_util.ativar_click_direito(self.handle)

            if self.buscar_imagem.buscar_item_simples(img_path):
                faltas = 0  # ainda está na tela
            else:
                faltas += 1
                if faltas >= faltas_necessarias:
                    self._registrar_abate()
                    return True  # sumiu de verdade

            time.sleep(intervalo)

        print('Saiu da tentativa de matar suicide em 180s!')
        return False

    def _tentar_pklizar(self) -> None:
        """
        1) Posiciona e ativa o ataque (botão direito).
        2) Procura sinal de PK por até 2s no total.
        3) Se encontrar, mantém PK ativo e vigia ESSA mesma imagem até sumir.
        4) Quando sumir, desativa PK e sai.
        """
        mouse_util.ativar_click_direito(self.handle)

        try:
            if self.mover_spot_util.esta_na_safe:
                print('3 - Morreu enqto procurava player')
                return

            # 1) busca inicial (2s TOTAL) para "travar" numa imagem base
            img_base = self._buscar_pk_cascata(prioridade=None, timeout_total=2.0, intervalo=0.10)

            if not img_base:
                print('NAO ACHOU SUICIDE')
                self._desativar_pk()
                return

            # 2) achou algo -> atacar
            print('ACHOU SUICIDE:', img_base)
            # if self.pointer.get_nome_char() != 'Narukami':
            self._ativar_pk()

            # 3) vigiar até sumir (oponente morto ou saiu da tela)
            sumiu = self._vigiar_imagem_ate_sumir(img_base, confirmar_desaparecimento_ms=400, intervalo=0.08)
            if sumiu:
                print('Imagem sumiu — oponente abatido.')
            else:
                print('Vigilância interrompida (provável morte / safe).')

        finally:
            self._desativar_pk()
            mouse_util.desativar_click_direito(self.handle)

    def _registrar_abate(self) -> None:
        with self._abates_lock:
            self._abates += 1
            print(f"[ABATE] +1 do {self.pointer.get_nome_char()} - (total={self._abates})")

    # ---------- Ações rápidas ----------
    def _ativar_skill(self):
        self.teclado_util.selecionar_skill_3()
        mouse_util.clickDireito(self.handle)
        self.teclado_util.selecionar_skill_1()

    def _ativar_pk(self):
        if self.pointer.get_pk_ativo() == 0:
            self.teclado_util.combo_tecla("LCTRL", "LSHIFT")

    def _desativar_pk(self):
        if self.pointer.get_pk_ativo() == 1:
            self.teclado_util.combo_tecla("LCTRL", "LSHIFT")
