import math
import random
import threading
import time
from abc import ABC, abstractmethod
from typing import Optional, Sequence, Union
from typing import Tuple, Callable, List

import win32gui

from interface_adapters.helpers.session_manager_new import Sessao, GenericoFields
from interface_adapters.up.up_util.up_util import Up_util
from services.alterar_char_sala_service import AlterarCharSalaService
from services.buscar_personagem_proximo_service import BuscarPersoangemProximoService
from services.posicionamento_spot_service import PosicionamentoSpotService
from services.verificador_imagem_userbar import VerificadorImagemUseBar
from utils import screenshot_util, mouse_util, spot_util
from utils.buscar_item_util import BuscarItemUtil
from utils.json_file_manager_util import JsonFileManager
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers
from utils.rota_util import PathFinder
from utils.teclado_util import Teclado_util


class PkBase(ABC):
    """
    Classe base para estratégias de PK.
    - Mantém dependências (handle, sessao, ponteiros, utils).
    - Fornece utilitários comuns: checagem de /info, fluxo de executar rota de spots,
      mecanismo de ataque e vigilância de imagens.
    OBS: não alterar o nome da classe nem do método execute().
    """

    CAMINHO_PK0 = './static/pk/pk0.png'
    CAMINHO_PK1 = './static/pk/pk1.png'
    CAMINHO_OKINFO = './static/pk/okinfo.png'

    def __init__(self, handle, arduino, mapa):
        # contexto e dependências
        self.handle = handle
        self.sessao = Sessao(handle=handle)
        self.pointer = Pointers(handle)
        self.classe_personagem = self.sessao.ler_generico(GenericoFields.CLASSE_PERSONAGEM)
        self.titulo_janela = win32gui.GetWindowText(handle)
        self.mapa = mapa

        # utilitários
        self.teclado = Teclado_util(self.handle, arduino)
        self.mover_spot = MoverSpotUtil(self.handle)
        self.up = Up_util(self.handle, pointer=self.pointer, conexao_arduino=arduino)
        self.servico_buscar_personagem = BuscarPersoangemProximoService(self.pointer)
        self.buscar_imagem = BuscarItemUtil(self.handle)
        self.verificador_imagem_usebar = VerificadorImagemUseBar()

        # json de personagens
        self._arquivo_personagens = "./data/personagens.json"
        self.json_manager = JsonFileManager(self._arquivo_personagens)
        self.personagens = self.json_manager.read().get("Personagem", [])

        # estado
        self.coord_mouse_atual: Optional[Tuple[int, int]] = None
        self.coord_spot_atual: Optional[Tuple[int, int]] = None
        self.tipo_pk: Optional[str] = None
        self._abates = 0
        self._abates_lock = threading.Lock()
        self.morreu = False

        # comando inicial
        self.teclado.escrever_texto('/re off')

        # definir tipo e senha (subclasse)
        senha = self._definir_tipo_pk_e_senha()
        self.alternar_sala = AlterarCharSalaService(handle, senha, arduino)

    # -----------------------
    # ciclo principal (public)
    # -----------------------
    def execute(self):
        """
        Loop principal: verifica se limpou pk; se limpou inicia pk, senão tenta limpar.
        Subclasses podem sobrescrever execute, mas por padrão esse loop simples funciona.
        """
        while True:
            limpou = self._verificar_se_limpo()
            if limpou is None:
                print("Erro ao ler info de PK. Repetindo...")
                continue

            if limpou:
                self.iniciar_pk()
                print("Aguardando 60s antes da próxima verificação...")
                time.sleep(60)
            else:
                self.limpar_pk()

    # -----------------------
    # métodos abstratos que SUBCLASSES devem implementar
    # -----------------------
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

    # -----------------------
    # utilitários públicos/compostos
    # -----------------------
    def executar_rota_pk(self, etapas: Sequence[Callable[[], List]]):
        """
        Recebe uma sequência de funções que retornam 'spots' (lista de grupos).
        Para cada etapa: obtém spots -> tenta executar pk nesses spots -> interrompe se morreu ou
        se pk_pode_continuar() retornar False.
        """
        self.morreu = False
        for func_obter_spots in etapas:
            spots = func_obter_spots()
            self._executar_pk(spots)
            if self.morreu or not self.pk_pode_continuar():
                return

    def pk_pode_continuar(self) -> bool:
        return bool(self._consultar_info_e_verificar((self.CAMINHO_PK1, self.CAMINHO_PK0)))

    def _consultar_info_e_verificar(
            self,
            imagens_pk: Union[str, Sequence[str]],
            timeout_okinfo: float = 8.0
    ) -> Optional[bool]:

        try:
            # bypass opcional
            if self.pointer.get_nome_char() == 'Narukami':
                return True

            # normaliza para sequência
            if isinstance(imagens_pk, str):
                lista_imgs = (imagens_pk,)
            else:
                # garante tuple para iteração estável
                lista_imgs = tuple(imagens_pk)

            # abre /info e espera aparecer o botão OK
            inicio = time.time()
            while True:
                mouse_util.mover(self.handle, 1, 1)
                self.teclado.escrever_texto("/info")
                time.sleep(0.8)

                if self.buscar_imagem.buscar_item_simples(self.CAMINHO_OKINFO):
                    break

                if time.time() - inicio > timeout_okinfo:
                    print("[WARN] /info não apareceu (OK não encontrado).")
                    return None

            # checa qualquer imagem de PK
            achou = any(self._eh_pk(caminho) for caminho in lista_imgs)

            # fecha /info clicando no OK (melhor esforço)
            self._mover_e_clicar_na_opcao(self.CAMINHO_OKINFO)

            return achou

        except Exception as e:
            print("Erro em _consultar_info_e_verificar:", e)
            return None

    def _verificar_se_limpo(self) -> Optional[bool]:
        return self._consultar_info_e_verificar(self.CAMINHO_PK0)

    def _eh_pk(self, caminho_imagem: str) -> bool:
        screenshot = screenshot_util.capture_region(self.handle, 350, 270, 80, 25)
        return bool(self.buscar_imagem.buscar_posicoes_de_item(caminho_imagem, screenshot, precisao=.9))

    def _mover_e_clicar_na_opcao(self, caminho_imagem: str, timeout: float = 5.0) -> bool:
        """
        Move mouse pra canto, procura o botão (imagem) e clica até a imagem desaparecer (com debounce).
        Retorna True se confirmou desaparecimento, False caso timeout.
        """
        mouse_util.mover(self.handle, 1, 1)
        inicio = time.time()
        ja_clicou = False

        while time.time() - inicio < timeout:
            pos = self.buscar_imagem.buscar_item_simples(caminho_imagem)
            if pos:
                mouse_util.left_clique(self.handle, *pos)
                ja_clicou = True
                time.sleep(0.15)
                continue

            if ja_clicou and pos is None:
                return True

            time.sleep(0.1)

        return False

    # -----------------------
    # rotina de limpeza de PK
    # -----------------------
    def limpar_pk(self):
        """
        Movimento para sala 2, desativa PK, ativa UP, busca spot vazio e vigia até estar limpo.
        Se morrer, aguarda tempo randômico e repete.
        """
        self.mover_para_sala2()
        self._desativar_pk()
        self.teclado.escrever_texto('/re off')
        self.up.ativar_desc_item_spot()
        self.mover_para_spot_vazio()

        ultimo_check_up = time.time()
        ultimo_check_pk = time.time()

        while True:
            # reativa up a cada ~0.5s
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
                limpou = self._verificar_se_limpo()
                if limpou:
                    self.mover_para_sala7()
                    return

            self._corrigir_coordenada_e_mouse()

    def mover_para_sala2(self):
        if self.pointer.get_sala_atual() != 2:
            self.alternar_sala.selecionar_sala(2)

    def mover_para_sala7(self):
        if self.pointer.get_sala_atual() != 7:
            self.alternar_sala.selecionar_sala(7)

    def mover_para_sala(self, sala):
        if self.pointer.get_sala_atual() != sala:
            self.alternar_sala.selecionar_sala(sala)

    def mover_para_spot_vazio(self):
        self.teclado.selecionar_skill_1()
        self._sair_da_safe()

        if self.mapa == PathFinder.MAPA_AIDA:
            spots = spot_util.buscar_spots_aida_2()
        elif self.mapa == PathFinder.MAPA_TARKAN:
            spots = spot_util.buscar_spots_todos_tk(nao_ignorar_spot_pk=True)
        elif self.mapa == PathFinder.MAPA_KANTURU_1_E_2:
            self.mapa = PathFinder.MAPA_TARKAN
            spots = spot_util.buscar_spots_todos_tk()
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
        for indice_spot, grupo_de_spots in enumerate(spots):
            for grupo in grupo_de_spots:
                classes, coordenadas_spot, coordenada_mouse = grupo

                if 'SM' not in classes:
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

                proximos = self.servico_buscar_personagem.ordenar_proximos(resultados, limite=20)
                for registro in proximos:
                    nome = registro.get("nome", "")
                    x = registro.get("x", 0)
                    y = registro.get("y", 0)

                    posicionou = self._posicionar_char_pklizar(x, y)
                    if posicionou:
                        self._tentar_pklizar(nome)
                    else:
                        print('MORREU ENQUANTO POSICIONAVA!')
                        self.morreu = True
                        return

    def _verificar_se_eh_tohell(self, nome):
        return self.verificador_imagem_usebar.verificar_pasta(nome, "./static/usebar/tohell/")

    def _buscar_pk_cascata(self, prioridade: Optional[str] = None, timeout_total: float = 2.0,
                           intervalo: float = 0.10) -> Optional[str]:
        """
        Varre uma lista de imagens de PK por até timeout_total segundos.
        Se 'prioridade' fornecida, checa-a antes das demais.
        Retorna o caminho da imagem encontrada ou None.
        """
        imagens = [
            './static/pk/suiciide.png',
            './static/pk/suici.png',
            './static/pk/suic.png',
            './static/pk/suicide.png',
            './static/pk/suicide2.png',
        ]

        # exclusivos da sala 7
        if self.pointer.get_sala_atual() == 7:
            imagens += [
                './static/pk/loja.png',
                './static/pk/fenix.png',
            ]

        deadline = time.monotonic() + timeout_total
        while time.monotonic() < deadline:
            if prioridade and self.buscar_imagem.buscar_item_simples(prioridade):
                return prioridade

            for img in imagens:
                if img == prioridade:
                    continue
                if self.buscar_imagem.buscar_item_simples(img):
                    return img

            time.sleep(intervalo)
        return None

    def _vigiar_imagem_ate_sumir(self, caminho_img: str, confirmar_desaparecimento_ms: int = 400,
                                 intervalo: float = 0.08) -> bool:
        """
        Observa a mesma imagem até confirmar que desapareceu.
        Usa debounce (faltas consecutivas) para evitar falsos positivos.
        Retorna True se confirmado sumiço; False se interrompido (ex.: morreu).
        """
        faltas_necessarias = max(1, math.ceil(confirmar_desaparecimento_ms / (intervalo * 1000)))
        faltas = 0
        deadline = time.monotonic() + 30  # timeout genérico 30s

        while time.monotonic() < deadline:
            if self.mover_spot.esta_na_safe:
                print('Morreu enquanto vigiava o oponente')
                return False

            if self.mapa == PathFinder.MAPA_AIDA:
                self.teclado.tap_tecla("Q")

            mouse_util.ativar_click_direito(self.handle)

            if self.buscar_imagem.buscar_item_simples(caminho_img):
                faltas = 0
            else:
                faltas += 1
                if faltas >= faltas_necessarias:
                    self._registrar_abate()
                    return True

            time.sleep(intervalo)

        print('Tempo excedido (30s) ao vigiar imagem.')
        return False

    def _tentar_pklizar(self, nome) -> None:
        mouse_util.ativar_click_direito(self.handle)
        try:
            if self.mover_spot.esta_na_safe:
                print('Morreu enquanto procurava player')
                return

            if self._verificar_se_eh_tohell(nome):
                return

            # img_base = self._buscar_pk_cascata(prioridade=None, timeout_total=2.0, intervalo=0.10)
            # if not img_base:
            #     print('Não encontrou alvo para PK')
            #     self._desativar_pk()
            #     return

            if self.pointer.get_char_pk_selecionado() is None:
                print('Não encontrou alvo para PK')
                self._desativar_pk()
            else:
                print('Alvo detectado')
                self._ativar_pk()

            # sumiu = self._vigiar_imagem_ate_sumir(img_base, confirmar_desaparecimento_ms=400, intervalo=0.08)
            sumiu = self._pklizar()
            if sumiu:
                print('Oponente abatido.')
            else:
                print('Vigilância interrompida (provável morte/safe).')

        finally:
            mouse_util.desativar_click_direito(self.handle)
            self._desativar_pk()

    def _pklizar(self, confirmar_desaparecimento_ms: int = 400,
                 intervalo: float = 0.08) -> bool:

        faltas_necessarias = max(1, math.ceil(confirmar_desaparecimento_ms / (intervalo * 1000)))
        faltas = 0

        tempo = 10
        deadline = time.monotonic() + tempo
        while time.monotonic() < deadline:
            if self.mover_spot.esta_na_safe:
                print('Morreu enquanto matava o char no spot!')
                return False

            if self.mapa == PathFinder.MAPA_AIDA or self.mapa == PathFinder.MAPA_KANTURU_1_E_2:
                self.teclado.tap_tecla("Q")

            mouse_util.ativar_click_direito(self.handle)

            if self.pointer.get_char_pk_selecionado():
                faltas = 0
            else:
                faltas += 1
                if faltas >= faltas_necessarias:
                    self._registrar_abate()
                    return True

            time.sleep(intervalo)

        print('Tempo excedido (' + str(tempo) + 's) ao tentar pklizar.')
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
