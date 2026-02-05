import time

import requests
import win32gui

from interface_adapters.up.up_util.up_util import Up_util
from services.buscar_personagem_proximo_service_old import BuscarPersoangemProximoService
from sessao_handle import get_handle_atual
from utils import mouse_util
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers
from utils.rota_util import PathFinder
from utils.teclado_util import Teclado_util


class PklizarService:

    def __init__(self, mapa):
        self.handle = get_handle_atual()
        self.pointer = Pointers()
        self.mapa = mapa

        self.classe = self.pointer.get_classe()
        self.titulo_janela = win32gui.GetWindowText(self.handle)
        self.up_util = Up_util()
        self.servico_buscar_personagem = BuscarPersoangemProximoService()
        self.teclado = Teclado_util()
        self.mover_spot = MoverSpotUtil()

        self.lista_player_tohell = None
        self.lista_player_suicide = None

    def execute(self, ativar_pk=False, nivel_pk=100):
        if nivel_pk != 100 and self.pointer.get_nivel_pk() >= nivel_pk:
            return

        try:
            proximos = self.buscar_players_para_pklizar()
            if proximos:

                if ativar_pk:
                    self.ativar_pk()

                if nivel_pk == 1:
                    proximos = proximos[:1]

                for registro in proximos:
                    nome = registro.get("nome", "")
                    x = registro.get("x", 0)
                    y = registro.get("y", 0)

                    if self._verificar_se_eh_tohell(nome):
                        continue

                    if self.pointer.get_sala_atual() == 7 or self._verificar_se_eh_suicide(nome):

                        posicionou = self._posicionar_char_pklizar(x, y)
                        if posicionou:
                            pklizou = self._tentar_pklizar()
                            if not pklizou:
                                return False
                        else:
                            print('MORREU ENQUANTO POSICIONAVA!')
                            return False
                    else:
                        print('Continuando procura de suicide...')
                        continue
        finally:

            if ativar_pk:
                self.desativar_pk()

    def ativar_pk(self) -> bool:
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

    def desativar_pk(self) -> bool:
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

    def buscar_players_para_pklizar(self):
        resultados = self.servico_buscar_personagem.listar_nomes_e_coords_por_padrao()
        if resultados:
            proximos = self.servico_buscar_personagem.ordenar_proximos(resultados, 30)
            if len(proximos) >= 3:
                proximos = proximos[:3]
            return proximos
        return None

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

    def _posicionar_char_pklizar(self, x: int, y: int):
        mouse_util.desativar_click_direito(self.handle)  # DESATIVA PARA EVITAR BUG MOVIMENTACAO
        return self.mover_spot.movimentar(
            (y, x),
            verficar_se_movimentou=True,
            posicionar_mouse_coordenada=True
        )

    def _tentar_pklizar(self):  # DEVE RETORNAR TRUE PARA CONTINUAR COM A PKLIZACAO
        try:
            if self.mover_spot.esta_na_safe:
                print('Morreu enquanto procurava player')
                return False

            time.sleep(.25)  # DA O TEMPO DE CARREGAR A SELEÇÃO DO MOUSE NO CHAR

            if self.pointer.get_char_pk_selecionado() is False:
                print('Não encontrou alvo para PK')
                return True
            else:
                print('Alvo detectado')

            sumiu = self._pklizar()
            if sumiu:
                print('Oponente abatido.')
            else:
                print('Vigilância interrompida (provável morte/safe).')

            return True

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
                    return True

            time.sleep(intervalo)

        print(f'Tempo excedido ({tempo_total_s}s) ao tentar pklizar.')
        return False

    def atualizar_lista_player(self):
        self.atualizar_lista_tohell()
        self.atualizar_lista_suicide()

    def atualizar_lista_tohell(self):
        try:
            r = requests.get("http://192.168.101.14:8000/players?rival=nao&offset=0&limit=10000", timeout=10)
            r.raise_for_status()
            self.lista_player_tohell = r.json().get("items", [])
        except Exception as e:
            print(f"[ERRO] Falha ToHeLL: {e}")
            exit()

    def atualizar_lista_suicide(self):
        try:
            r = requests.get("http://192.168.101.14:8000/players?rival=sim&offset=0&limit=10000", timeout=10)
            r.raise_for_status()
            items = r.json().get("items", [])
            self.lista_player_suicide = items
        except Exception as e:
            print(f"[ERRO] Falha Suicide: {e}")
            exit()

    def eh_char_bloqueado(self, nome: str) -> bool:
        nomes_bloqueados = {
            "Dynast_", "Dynasty_", "Baal", "OverNight",
            "INFECTRIX", "SisteMatyc", "SM_Troyer", "AlfaVictor", "LAZLU", "_Offensive"
        }
        return any(nome_bloqueado in nome for nome_bloqueado in nomes_bloqueados)
