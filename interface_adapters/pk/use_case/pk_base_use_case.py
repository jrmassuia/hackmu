import time
from abc import ABC, abstractmethod
from typing import Optional, Sequence, Tuple

import win32gui

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

        # Define tipo e senha (fornecidos pela subclasse)
        senha = self._definir_tipo_pk_e_senha()

        # Serviço de alternância de sala
        self.alternar_sala = AlterarCharSalaService(handle, senha, arduino)

    # ---------- Métodos de ciclo externo ----------
    def execute(self):
        """Loop principal: lê PK -> se limpo, inicia PK; senão, rotina de limpar PK."""
        while True:
            limpou_pk = self.ler_pk()
            if limpou_pk is None:
                print("erro leitura pk")
                continue

            if limpou_pk:
                self.iniciar_pk()
                # Mantém a pausa para finalizar autodefesa (original)
                if self.pointer.get_nome_char() != 'Narukami':
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

    # ---------- Utilitários comuns ----------
    def _consultar_info_e_verificar(self, imagem_pk: str) -> bool:
        """
        Fluxo comum: mover mouse -> /info -> aguardar -> verificar imagem-alvo (pk0/pk1)
        -> clicar OK -> retornar True/False conforme encontrado.
        Mantém a lógica original, com limpeza de pequenas arestas.
        """
        if self.pointer.get_nome_char() == 'Narukami':
            return True  # early return preservado

        mouse_util.mover(self.handle, 1, 1)  # tira o mouse da tela
        # Abre /info até o botão OK aparecer
        while True:
            self.teclado_util.escrever_texto("/info")
            time.sleep(1)
            achou_btn = self.buscar_imagem.buscar_item_simples(self.IMG_OKINFO)
            if achou_btn:
                break

        achou = self._eh_pk(imagem_pk)
        # Fecha o /info de forma robusta
        self._mover_e_clicar_na_opcao(self.IMG_OKINFO)
        return bool(achou)

    def ler_pk(self) -> Optional[bool]:
        return self._consultar_info_e_verificar(self.IMG_PK0)

    def _pk_pode_continuar(self) -> bool:
        return self._consultar_info_e_verificar(self.IMG_PK1) or self._consultar_info_e_verificar(self.IMG_PK0)

    def _eh_pk(self, image_path: str) -> bool:
        screenshot = screenshot_util.capture_region(self.handle, 350, 270, 80, 25)
        return bool(self.buscar_imagem.buscar_posicoes_de_item(image_path, screenshot, precisao=.9))

    def _mover_e_clicar_na_opcao(self, imagem_path: str, timeout: float = 60.0) -> bool:
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
                print('Esperando na safe...')
                time.sleep(120)
                self.mover_para_spot_vazio()

            # a cada 180s, checa se limpou PK
            if time.time() - ultimo_check_pk >= 180:
                ultimo_check_pk = time.time()
                limpou_pk = self.ler_pk()
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
            spots = spot_util.buscar_spots_tk2()
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
                        print('POSICIONOU!')
                        time.sleep(1)

                        while True:
                            if self.mover_spot_util.esta_na_safe:
                                print('3 - Morreu enqto procurava player')
                                return

                            if self._pode_pklizar():
                                print('ACHOU SUICIDE')
                                if self.pointer.get_nome_char() == 'Narukami':
                                    time.sleep(3)
                                    break
                                else:
                                    self._ativar_pk()
                                    mouse_util.ativar_click_direito(self.handle)
                                    self.teclado_util._toque_arduino("Q")
                                    time.sleep(.25)
                            else:
                                print('NAO ACHOU SUICIDE')
                                self._desativar_pk()
                                break
                    else:
                        print('NÃO POSICIONOU!')

                    mouse_util.desativar_click_direito(self.handle)

    # ---------- Heurísticas visuais ----------
    def _pode_pklizar(self) -> bool:
        screenshot = screenshot_util.capture_window(self.handle)
        eh_suicide = self.buscar_imagem.buscar_posicoes_de_item('./static/pk/suicide.png', screenshot, precisao=.7)
        eh_suiciide = self.buscar_imagem.buscar_posicoes_de_item('./static/pk/suiciide.png', screenshot, precisao=.7)
        eh_loja = self.buscar_imagem.buscar_posicoes_de_item('./static/pk/loja.png', screenshot, precisao=.7)
        return bool(eh_suicide or eh_suiciide or eh_loja)

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
