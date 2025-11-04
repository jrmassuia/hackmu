import random
import threading
import time
from abc import ABC, abstractmethod
from typing import Optional, Sequence
from typing import Tuple, Callable, List

import requests
import win32gui

from interface_adapters.helpers.session_manager_new import Sessao, GenericoFields
from interface_adapters.up.up_util.up_util import Up_util
from services.alterar_char_sala_service import AlterarCharSalaService
from services.buscar_personagem_proximo_service import BuscarPersoangemProximoService
from services.posicionamento_spot_service import PosicionamentoSpotService
from utils import mouse_util, spot_util
from utils.buscar_item_util import BuscarItemUtil
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers
from utils.rota_util import PathFinder
from utils.teclado_util import Teclado_util


class PkBase(ABC):

    def __init__(self, handle, arduino, mapa):
        # contexto e dependências
        self.handle = handle
        self.sessao = Sessao(handle=handle)
        self.pointer = Pointers(handle)
        self.classe_personagem = self.sessao.ler_generico(GenericoFields.CLASSE_PERSONAGEM)
        self.titulo_janela = win32gui.GetWindowText(handle)
        self.up_util = Up_util(self.handle, pointer=self.pointer, conexao_arduino=arduino)
        self.mapa = mapa

        # utilitários
        self.teclado = Teclado_util(self.handle, arduino)
        self.mover_spot = MoverSpotUtil(self.handle)
        self.up = Up_util(self.handle, pointer=self.pointer, conexao_arduino=arduino)
        self.servico_buscar_personagem = BuscarPersoangemProximoService(self.pointer)
        self.buscar_imagem = BuscarItemUtil(self.handle)

        # estado
        self.coord_mouse_atual: Optional[Tuple[int, int]] = None
        self.coord_spot_atual: Optional[Tuple[int, int]] = None
        self.tipo_pk: Optional[str] = None
        self._abates = 0
        self._abates_lock = threading.Lock()
        self.morreu = False
        self.lista_player_tohell = None
        self.lista_player_suicide = None

        # comando inicial
        self.teclado.escrever_texto('/re off')

        # definir tipo e senha (subclasse)
        senha = self._definir_tipo_pk_e_senha()
        self.alternar_sala = AlterarCharSalaService(handle, senha, arduino)

    def execute(self):
        while True:
            limpou = self._verificar_se_limpou()
            if limpou is None:
                print("Erro ao ler info de PK. Repetindo...")
                continue

            if limpou:
                self.atualizar_lista_player()
                self.iniciar_pk()
            else:
                self.limpar_pk()

    @abstractmethod
    def _definir_tipo_pk_e_senha(self) -> str:
        """Subclasse define self.tipo_pk e retorna senha (string)."""
        raise NotImplementedError()

    @abstractmethod
    def iniciar_pk(self) -> None:
        """Fluxo que inicia uma rotina de PK (por mapa/tipo)."""
        raise NotImplementedError()

    @abstractmethod
    def _corrigir_coordenada_e_mouse(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def _esta_na_safe(self) -> bool:
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

    def atualizar_lista_player(self):
        self.atualizar_lista_tohell()
        self.atualizar_lista_suicide()

    def atualizar_lista_tohell(self):
        try:
            r = requests.get("http://192.168.101.14:8000/tohell/players?offset=0&limit=1000", timeout=10)
            r.raise_for_status()
            self.lista_player_tohell = r.json().get("items", [])
        except Exception as e:
            print(f"[ERRO] Falha ToHeLL: {e}")
            exit()

    def atualizar_lista_suicide(self):
        try:
            r = requests.get("http://192.168.101.14:8000/suicide/players?offset=0&limit=1000", timeout=10)
            r.raise_for_status()
            self.lista_player_suicide = r.json().get("items", [])
        except Exception as e:
            print(f"[ERRO] Falha Suicide: {e}")
            exit()

    def executar_rota_pk(self, etapas: Sequence[Callable[[], List]]):
        self.morreu = False
        for func_obter_spots in etapas:
            spots = func_obter_spots()
            self._executar_pk(spots)
            if self.morreu or not self.verificar_se_pode_continuar_com_pk():
                return False
            else:
                self.up_util.limpar_mob_ao_redor(None, None)
        return True

    def _verificar_se_limpou(self) -> Optional[bool]:
        nivel_pk = self.up_util.verificar_nivel_pk()
        if (self.pointer.get_sala_atual() == 2 and nivel_pk == 0) or (
                self.pointer.get_sala_atual() != 2 and nivel_pk <= 1):
            return True
        else:
            return False

    def verificar_se_pode_continuar_com_pk(self) -> Optional[bool]:
        nivel_pk = self.up_util.verificar_nivel_pk()
        if nivel_pk <= 1:
            return True
        return False

    def limpar_pk(self):
        if self.pointer.get_sala_atual() != 2:  # NECESSARIO FINALIZAR ATIVAÇAO DO PK PARA IR SALA 2
            print("Aguardando 60s para ir limpar PK...")
            time.sleep(60)
        self.mover_para_sala(2)
        self._desativar_pk()
        self.teclado.escrever_texto('/re off')
        self.up.ativar_desc_item_spot()
        self.mover_para_spot_vazio()

        ultimo_check_up = time.time()
        ultimo_check_pk = time.time()

        while True:
            if time.time() - ultimo_check_up >= 0.5:
                self.up.ativar_up()
                ultimo_check_up = time.time()

            if self._esta_na_safe():
                self.morreu = True

            if self.morreu:
                espera = random.randint(3 * 60, 10 * 60)
                print(f"Aguardando {espera // 60} minutos ({espera}s) - {self.titulo_janela}")
                time.sleep(espera)
                self.mover_para_spot_vazio()

            # checar PK a cada 180s
            if time.time() - ultimo_check_pk >= 180:
                ultimo_check_pk = time.time()
                limpou = self._verificar_se_limpou()
                if limpou:
                    self.mover_para_sala(7)
                    return

            self._corrigir_coordenada_e_mouse()

    def mover_para_sala(self, sala):
        if self.pointer.get_sala_atual() != sala:
            self.alternar_sala.selecionar_sala(sala)

    def mover_para_spot_vazio(self):
        self.teclado.selecionar_skill_1()
        self._sair_da_safe()

        if self.mapa == PathFinder.MAPA_AIDA:
            spots = spot_util.buscar_spots_aida_2()
        elif self.mapa == PathFinder.MAPA_TARKAN:
            spots = spot_util.buscar_todos_spots_tk(nao_ignorar_spot_pk=True)
        elif self.mapa == PathFinder.MAPA_KANTURU_1_E_2:
            self.mapa = PathFinder.MAPA_TARKAN
            spots = spot_util.buscar_todos_spots_tk()
        else:
            spots = []

        posicionador = PosicionamentoSpotService(
            self.handle,
            self.pointer,
            self.mover_spot,
            self.classe_personagem,
            None,
            spots,
            self.mapa
        )

        achou = posicionador.posicionar_bot_up()
        if achou:
            self.coord_mouse_atual = posicionador.get_coord_mouse()
            self.coord_spot_atual = posicionador.get_coord_spot()

        self.morreu = bool(self.mover_spot.esta_na_safe)

    def _executar_pk(self, spots: Sequence[Sequence]):
        try:
            self._ativar_pk()
            for indice_spot, grupo_de_spots in enumerate(spots):
                for grupo in grupo_de_spots:
                    classes, coordenadas_spot, coordenada_mouse = grupo

                    if 'DL' not in classes:
                        continue

                    coordenadas = coordenadas_spot[0]
                    movimentou = self._movimentar_char_spot(coordenadas)
                    if not movimentou:
                        print('Morreu enquanto procurava player - falha movimentação')
                        self.morreu = True
                        return

                    resultados = self.servico_buscar_personagem.listar_nomes_e_coords_por_padrao()
                    if not resultados:
                        continue

                    proximos = self.servico_buscar_personagem.ordenar_proximos(resultados, limite=30)
                    if len(proximos) >= 3:
                        proximos = proximos[:3]

                    for registro in proximos:
                        nome = registro.get("nome", "")
                        x = registro.get("x", 0)
                        y = registro.get("y", 0)

                        if self.morreu:
                            return

                        if self._verificar_se_eh_tohell(nome):
                            continue

                        if self.pointer.get_sala_atual() == 7 or self._verificar_se_eh_suicide(nome):

                            posicionou = self._posicionar_char_pklizar(x, y)
                            if posicionou:
                                self._tentar_pklizar()
                            else:
                                print('MORREU ENQUANTO POSICIONAVA!')
                                self.morreu = True
                                return
                        else:
                            print('Continuando procura de suicide...')
                            continue
        finally:
            self._desativar_pk()

    def _verificar_se_eh_tohell(self, nome):
        for player in self.lista_player_tohell:
            if player == nome:
                return True
        return False

    def _verificar_se_eh_suicide(self, nome):
        for player in self.lista_player_suicide:
            if player == nome:
                return True
        return False

    def _tentar_pklizar(self) -> None:
        try:
            if self.mover_spot.esta_na_safe:
                print('Morreu enquanto procurava player')
                self.morreu = True
                return

            time.sleep(.25)  # DA O TEMPO DE CARREGAR A SELEÇÃO DO MOUSE NO CHAR

            if self.pointer.get_char_pk_selecionado() is False:
                print('Não encontrou alvo para PK')
                return
            else:
                print('Alvo detectado')

            sumiu = self._pklizar()
            if sumiu:
                print('Oponente abatido.')
            else:
                print('Vigilância interrompida (provável morte/safe).')

        finally:
            mouse_util.desativar_click_direito(self.handle)

    def _pklizar(self, confirmar_desaparecimento_ms: int = 1000,
                 intervalo: float = 0.08) -> bool:

        tempo_total_s = 15
        deadline = time.monotonic() + tempo_total_s

        # Marca do último instante em que o alvo foi visto selecionado
        ultimo_visto_selecionado = time.monotonic()

        # (Opcional) ritma o 'Q' para não spammar a cada loop
        proximo_tap_q = 0.0
        intervalo_q = 0.2  # segundos

        while time.monotonic() < deadline:
            if self.mover_spot.esta_na_safe:
                print('Morreu enquanto matava o char no spot!')
                self.morreu = True
                return False

            agora = time.monotonic()

            # Usa Q só onde precisa e com ritmo
            if (self.mapa == PathFinder.MAPA_AIDA or
                    self.mapa == PathFinder.MAPA_KANTURU_1_E_2):
                if agora >= proximo_tap_q:
                    self.teclado.tap_tecla("Q")
                    proximo_tap_q = agora + intervalo_q

            # Mantém pressão do direito (se for a sua estratégia)
            mouse_util.ativar_click_direito(self.handle)

            selecionado = self.pointer.get_char_pk_selecionado()

            if selecionado:
                # Reset do relógio de “ausência”
                ultimo_visto_selecionado = agora
            else:
                desaparecido_ms = (agora - ultimo_visto_selecionado) * 1000.0
                if desaparecido_ms >= confirmar_desaparecimento_ms:
                    # self._registrar_abate()
                    return True

            time.sleep(intervalo)

        print(f'Tempo excedido ({tempo_total_s}s) ao tentar pklizar.')
        return False

    def _registrar_abate(self) -> None:
        with self._abates_lock:
            self._abates += 1
            print(f"[ABATE] +1 do {self.pointer.get_nome_char()} - (total={self._abates})")

    def _ativar_skill(self):
        self.teclado.selecionar_skill_3()
        mouse_util.clickDireito(self.handle)
        self.teclado.selecionar_skill_1()

    def _ativar_pk(self) -> bool:
        try:
            if self.pointer.get_pk_ativo() == 1:
                return True
            self.teclado.combo_tecla("LCTRL", "LSHIFT")
            time.sleep(0.12)
            if self.pointer.get_pk_ativo() == 1:
                return True
            # segunda tentativa (simples)
            self.teclado.combo_tecla("LCTRL", "LSHIFT")
            time.sleep(0.12)
            return self.pointer.get_pk_ativo() == 1
        except Exception:
            return False

    def _desativar_pk(self) -> bool:
        try:
            if self.pointer.get_pk_ativo() == 0:
                return True
            self.teclado.combo_tecla("LCTRL", "LSHIFT")
            time.sleep(0.12)
            if self.pointer.get_pk_ativo() == 0:
                return True
            # segunda tentativa (simples)
            self.teclado.combo_tecla("LCTRL", "LSHIFT")
            time.sleep(0.12)
            return self.pointer.get_pk_ativo() == 0
        except Exception:
            return False
