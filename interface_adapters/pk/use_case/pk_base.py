import time

import win32gui

from interface_adapters.helpers.session_manager_new import Sessao, GenericoFields
from interface_adapters.up.up_util.up_util import Up_util
from services.alterar_char_sala_service import AlterarCharSalaService
from services.buscar_personagem_proximo_service import BuscarPersoangemProximoService
from services.posicionamento_spot_service import PosicionamentoSpotService
from utils import screenshot_util, mouse_util, spot_util, safe_util
from utils.buscar_item_util import BuscarItemUtil
from utils.json_file_manager_util import JsonFileManager
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers
from utils.rota_util import PathFinder
from utils.teclado_util import Teclado_util


class PkBase:
    """
    Classe base para rotina de PK em Aida, com leitura de PK, movimentação entre salas/spots,
    e execução de ataques conforme o tipo de PK configurado para o personagem atual.
    """

    # =========================
    #       CONSTANTES
    # =========================
    PKLIZAR_AIDA_1 = 'AIDA_1'
    PKLIZAR_AIDA_2 = 'AIDA_2'
    PKLIZAR_AIDA_CORREDOR = 'AIDA_CORREDOR'
    PKLIZAR_AIDA_FINAL = 'AIDA_FINAL'

    IMG_PK0 = './static/pk/pk0.png'
    IMG_PK1 = './static/pk/pk1.png'
    IMG_OKINFO = './static/pk/okinfo.png'

    # =========================
    #     CICLO DE VIDA
    # =========================
    def __init__(self, handle, arduino):
        # Contexto / dependências
        self.handle = handle
        self.sessao = Sessao(handle=handle)
        self.pointer = Pointers(handle)
        self.classe = self.sessao.ler_generico(GenericoFields.CLASSE_PERSONAGEM)
        self.tela = win32gui.GetWindowText(handle)

        # Utilitários
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
        self.coord_mouse_atual = None
        self.coord_spot_atual = None
        self.tipo_pk = None

        # Configura senha/tipo de PK conforme nome do char (mesma lógica, organizada)
        senha = self._definir_tipo_pk_e_senha()

        # Serviço de alternância de sala
        self.alternar_sala = AlterarCharSalaService(handle, senha, arduino)

    # =========================
    #     PÚBLICO / ENTRADA
    # =========================
    def execute(self):
        """Loop principal: lê PK, inicia/limpa PK conforme necessidade."""
        while True:
            limpou_pk = self.ler_pk()
            if limpou_pk is None:
                print("erro leitura pk")
                continue

            if limpou_pk:
                self.iniciar_pk()
                if self.pointer.get_nome_char() != 'Narukami':
                    time.sleep(60)  # Necessário para finalizar autodefesa
            else:
                self.limpar_pk()

    def _definir_tipo_pk_e_senha(self):
        """
        Mantém exatamente a mesma lógica de seleção de senha/tipo_pk baseada no nome do char,
        apenas encapsulada para organização.
        """
        #AIDA 1
        if self.pointer.get_nome_char() == 'AlfaVictor':
            senha = 'thiago123'
            self.tipo_pk = PkBase.PKLIZAR_AIDA_1
        elif self.pointer.get_nome_char() == 'ReiDav1':
            senha = 'romualdo12'
            self.tipo_pk = PkBase.PKLIZAR_AIDA_1

        #AIDA 2
        elif self.pointer.get_nome_char() == 'LAZLU':
            senha = 'bebe133171'
            self.tipo_pk = PkBase.PKLIZAR_AIDA_2
        elif self.pointer.get_nome_char() == 'DL_JirayA':
            senha = '134779'
            self.tipo_pk = PkBase.PKLIZAR_AIDA_2

        #AIDA FINAL
        elif self.pointer.get_nome_char() == '_Offensive':
            senha = 'kuChx98f'
            self.tipo_pk = PkBase.PKLIZAR_AIDA_FINAL

        else:
            senha = ''
        return senha

    # =========================
    #     FLUXO DE PK
    # =========================
    def iniciar_pk(self):
        """Sai da safe, ativa skill e executa rotina de PK conforme o tipo configurado."""
        self.mover_para_sala7()
        self._sair_da_safe()
        self._ativar_skil()

        if self.tipo_pk == PkBase.PKLIZAR_AIDA_1:
            self.pklizar_aida1()
        elif self.tipo_pk == PkBase.PKLIZAR_AIDA_2:
            self.pklizar_aida2()
        elif self.tipo_pk == PkBase.PKLIZAR_AIDA_CORREDOR:
            self.pklizar_aida_corredor()
        elif self.tipo_pk == PkBase.PKLIZAR_AIDA_FINAL:
            self.pklizar_aida_final()
        else:
            self.pklizar_aida1()

    def pklizar_aida1(self):
        spots = spot_util.buscar_spots_aida_1(ignorar_spot_pk=True)
        self._executar_pk(spots)

        if self._pk_pode_continuar():
            spots_extras = self.buscar_spot_extra_aida1()
            self._executar_pk(spots_extras)

        if self._pk_pode_continuar():
            spots = spot_util.buscar_spots_aida_corredor()
            self._executar_pk(spots)

    def pklizar_aida2(self):
        spots = spot_util.buscar_spots_aida_volta_final(ignorar_spot_pk=True)
        spots.extend(spot_util.buscar_spots_aida_2(ignorar_spot_pk=True))
        self._executar_pk(spots)

    def pklizar_aida_corredor(self):
        spots = spot_util.buscar_spots_aida_corredor()
        self._executar_pk(spots)

        if self._pk_pode_continuar():
            spots = self.buscar_spot_extra_aida1()
            self._executar_pk(spots)

        if self._pk_pode_continuar():
            spots = spot_util.buscar_spots_aida_1(ignorar_spot_pk=True)
            self._executar_pk(spots)

    def pklizar_aida_final(self):
        spots = spot_util.buscar_spots_aida_final()
        self._executar_pk(spots)

        if self._pk_pode_continuar():
            spots = spot_util.buscar_spots_aida_corredor()
            self._executar_pk(spots)

        if self._pk_pode_continuar():
            spots_extras = self.buscar_spot_extra_aida1()
            self._executar_pk(spots_extras)

    def buscar_spot_extra_aida1(self):
        """Mantém a mesma lógica: pega os 3 últimos registros dos spots de Aida 1."""
        spots = spot_util.buscar_spots_aida_1()
        start = max(0, len(spots) - 3)
        spots_extras = []
        for indice_spot in range(start, len(spots)):
            spots_extras.extend([spots[indice_spot]])
        return spots_extras

    # =========================
    #     LEITURA / ESTADO PK
    # =========================
    def _consultar_info_e_verificar(self, imagem_pk: str) -> bool:
        """
        Fluxo comum: mover mouse -> /info -> aguardar -> verificar imagem-alvo (pk0/pk1)
        -> clicar OK -> retornar True/False conforme encontrado.
        Mantém exatamente a mesma lógica dos métodos originais.
        """
        if self.pointer.get_nome_char() == 'Narukami':
            return True  # mesmo early return dos métodos anteriores

        mouse_util.mover(self.handle, 1, 1)  # tira o mouse da tela
        self.teclado_util.escrever_texto("/info")
        time.sleep(1)

        achou = self._eh_pk(imagem_pk)
        self._mover_e_clicar_na_opcao(self.IMG_OKINFO)
        return bool(achou)

    def ler_pk(self):
        return self._consultar_info_e_verificar(self.IMG_PK0)

    def _pk_pode_continuar(self):
        return self._consultar_info_e_verificar(self.IMG_PK1)

    def _eh_pk(self, image):
        screenshot = screenshot_util.capture_region(self.handle, 350, 270, 80, 25)
        eh_pk = self.buscar_imagem.buscar_posicoes_de_item(image, screenshot, precisao=.9)
        if eh_pk:
            return True
        return False

    def _mover_e_clicar_na_opcao(self, imagem_path, timeout=60):
        """
        Move o mouse, tenta localizar a imagem e clicar nela até sumir (mantida a mesma lógica).
        """
        mouse_util.mover(self.handle, 1, 1)
        start_time = time.time()
        achou = False
        while time.time() - start_time < timeout:
            posicao = BuscarItemUtil(self.handle).buscar_item_simples(imagem_path)

            if achou and posicao is None:
                return True
            else:
                achou = False

            if posicao:
                mouse_util.left_clique(self.handle, *posicao)
                achou = True

        return False

    def limpar_pk(self):
        """Rotina para limpar PK: sala 2, desativar PK, posicionar em spot vazio, ficar upando, checar PK periodicamente."""
        self.mover_para_sala2()
        self._desativar_pk()
        self.up_util.ativar_desc_item_spot()
        self.mover_para_spot_vazio()

        tempo_leitura_pk = 0
        inicio = 30
        while True:
            if time.time() - inicio >= 30:
                time.sleep(0.5)
                self.up_util.ativar_up()
            else:
                inicio = time.time()

            if self.morreu():
                print('Esperando na safe...')
                time.sleep(120)
                self.mover_para_spot_vazio()

            if (time.time() - tempo_leitura_pk) > 180:
                tempo_leitura_pk = time.time()
                limpou_pk = self.ler_pk()
                if limpou_pk:
                    self.mover_para_sala7()
                    return

            self._corrigir_coordenada_e_mouse()
            self.up_util.ativar_up()

    def mover_para_sala2(self):
        if self.pointer.get_sala_atual() != 2:
            self.alternar_sala.selecionar_sala(2)

    def mover_para_sala7(self):
        if self.pointer.get_sala_atual() != 7:
            self.alternar_sala.selecionar_sala(7)

    def mover_para_spot_vazio(self):
        self.teclado_util.selecionar_skill_1()
        self._sair_da_safe()

        spots = spot_util.buscar_spots_aida_2()
        poscionar = PosicionamentoSpotService(
            self.handle,
            self.pointer,
            self.mover_spot_util,
            self.classe,
            None,
            spots,
            PathFinder.MAPA_AIDA
        )

        achou_spot = poscionar.posicionar_bot_up()
        if achou_spot:
            self.coord_mouse_atual = poscionar.get_coord_mouse()
            self.coord_spot_atual = poscionar.get_coord_spot()

    def _corrigir_coordenada_e_mouse(self):
        if self.coord_spot_atual and self.coord_mouse_atual:
            self.mover_spot_util.movimentar_aida(
                self.coord_spot_atual,
                verficar_se_movimentou=True
            )
            mouse_util.mover(self.handle, *self.coord_mouse_atual)

    def morreu(self):
        return safe_util.aida(self.handle)

    def _executar_pk(self, spots):
        for indice_spot, grupo_de_spots in enumerate(spots):
            for grupo in grupo_de_spots:
                classes, coordenadas_spot, coordenada_mouse = grupo

                # Utiliza a classe SM para mirar no centro do spot
                if 'SM' not in classes:
                    continue

                coordenada = coordenadas_spot[0]
                movimentou = self.mover_spot_util.movimentar_aida(
                    coordenada,
                    max_tempo=600,
                    verficar_se_movimentou=True,
                    movimentacao_proxima=True,
                    limpar_spot_se_necessario=True
                )

                if not movimentou:
                    return

                resultados = self.buscar_personagem.listar_nomes_e_coords_por_padrao()
                if len(resultados) == 0:
                    continue

                char_proximos = self.buscar_personagem.ordenar_proximos(resultados, limite=20)

                for i, d in enumerate(char_proximos, 100):
                    nome = d.get("nome", "")
                    x = d.get("x", "")
                    y = d.get("y", "")

                    # ignora self e mobs específicos
                    if self.pointer.get_nome_char() == nome or nome in [
                        'Death Tree', 'Forest Orc', 'Death Rider', 'Guard Archer',
                        'Blue Golem', 'Hell Maine', 'Witch Queen'
                    ]:
                        continue

                    if safe_util.aida(self.handle):
                        return

                    posicionou = self.mover_spot_util.movimentar_aida(
                        (y, x),
                        verficar_se_movimentou=True,
                        posicionar_mouse_coordenada=True,
                        limpar_spot_se_necessario=True
                    )

                    if posicionou:
                        print('POSICIONOU!')
                        time.sleep(1)

                        while True:
                            if self._pode_pklizar():
                                print('ACHOU SUICIDE')
                                if self.pointer.get_nome_char() == 'Narukami':
                                    time.sleep(3)
                                    break
                                else:
                                    self._ativar_pk()
                                    mouse_util.ativar_click_direito(self.handle)
                                    self.teclado_util._toque_arduino("Q")
                            else:
                                print('NAO ACHOU SUICIDE')
                                self._desativar_pk()
                                break
                    else:
                        print('NÃO POSICIONOU!')

                    mouse_util.desativar_click_direito(self.handle)

    def _pode_pklizar(self):
        screenshot = screenshot_util.capture_window(self.handle)
        eh_suicide = self.buscar_imagem.buscar_posicoes_de_item('./static/pk/suicide.png', screenshot, precisao=.7)
        eh_suiciide = self.buscar_imagem.buscar_posicoes_de_item('./static/pk/suiciide.png', screenshot, precisao=.7)
        eh_loja = self.buscar_imagem.buscar_posicoes_de_item('./static/pk/loja.png', screenshot, precisao=.7)
        return eh_suicide or eh_suiciide or eh_loja

    def _sair_da_safe(self):
        if safe_util.aida(self.handle):
            self._desbugar_goblin()
            self.mover_spot_util.movimentar_aida((100, 10), max_tempo=10, movimentacao_proxima=True)

    def _desbugar_goblin(self):
        btn_fechar = self.buscar_imagem.buscar_item_simples('./static/img/fechar_painel.png')
        if btn_fechar:
            x, y = btn_fechar
            mouse_util.left_clique(self.handle, x, y)
            time.sleep(1)
            mouse_util.left_clique(self.handle, 38, 369)

    def _ativar_skil(self):
        if self.classe == 'DL':
            self.teclado_util.selecionar_skill_3()
            mouse_util.clickDireito(self.handle)
            self.teclado_util.selecionar_skill_1()

    def _ativar_pk(self):
        if self.pointer.get_pk_ativo() == 0:
            self.teclado_util.combo_tecla("LCTRL", "LSHIFT")

    def _desativar_pk(self):
        if self.pointer.get_pk_ativo() == 1:
            self.teclado_util.combo_tecla("LCTRL", "LSHIFT")
