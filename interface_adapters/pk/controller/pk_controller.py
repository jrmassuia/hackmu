import time

import win32gui

import testeautopk
from interface_adapters.helpers.session_manager_new import Sessao, GenericoFields
from interface_adapters.up.up_util.up_util import Up_util
from services.alterar_char_sala_service import AlterarCharSalaService
from services.posicionamento_spot_service import PosicionamentoSpotService
from utils import screenshot_util, mouse_util, spot_util, safe_util, buscar_item_util
from utils.buscar_item_util import BuscarItemUtil
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers
from utils.rota_util import PathFinder
from utils.teclado_util import Teclado_util


class PKController:

    def __init__(self, handle, arduino, senha):
        self.handle = handle
        self.sessao = Sessao(handle=handle)
        self.pointer = Pointers(handle)
        self.classe = self.sessao.ler_generico(GenericoFields.CLASSE_PERSONAGEM)
        self.tela = win32gui.GetWindowText(handle)
        self.teclado_util = Teclado_util(self.handle, arduino)
        self.mover_spot_util = MoverSpotUtil(self.handle)
        self.up_util = Up_util(self.handle, pointer=self.pointer, conexao_arduino=arduino)
        self.coord_mouse_atual = None
        self.coord_spot_atual = None

        if self.pointer.get_nome_char() == 'AlfaVictor':
            senha = 'thiago123'
        elif self.pointer.get_nome_char() == 'ReiDav1':
            senha = 'romualdo12'

        self.alternar_sala = AlterarCharSalaService(self.handle, senha, arduino)


    def execute(self):
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

    def ler_pk(self):
        mouse_util.mover(self.handle, 1, 1)  # TIRA MOUSE DA TELA
        self.teclado_util.escrever_texto("/info")
        time.sleep(1)
        regiao_img = screenshot_util.capture_region(self.handle, 350, 270, 80, 25)
        limpou_pk0 = screenshot_util.is_image_in_region(regiao_img, './static/pk/pk0.png', threshold=.8)
        limpou_pk1 = screenshot_util.is_image_in_region(regiao_img, './static/pk/pk1.png', threshold=.8)
        self._mover_e_clicar_na_opcao('./static/pk/okinfo.png')
        if limpou_pk0 or limpou_pk1:
            return True
        return False

    def _mover_e_clicar_na_opcao(self, imagem_path, timeout=60):
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
        self.mover_para_sala2()
        self._desativar_pk()
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
                time.sleep(120)  # 180s
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
        self.alternar_sala.selecionar_sala(2)

    def mover_para_spot_vazio(self):
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

    def mover_para_sala7(self):
        self.alternar_sala.selecionar_sala(7)

    def iniciar_pk(self):
        self._sair_da_safe()
        self._ativar_skil()
        spots = spot_util.buscar_spots_aida_1(ignorar_spot_pk=True)
        self._executar_pk(spots)
        spots_extras = self.buscar_spot_extra_aida1()
        if self.ler_pk():
            self._executar_pk(spots_extras)

    def _executar_pk(self, spots):
        for indice_spot, grupo_de_spots in enumerate(spots):
            for grupo in grupo_de_spots:
                classes, coordenadas_spot, coordenada_mouse = grupo

                if 'SM' not in classes:  # UTILIZA A CLASSE SM PARA QUE OLHE NO CENTRO DO SPOT
                    continue

                coordenada = coordenadas_spot[0]
                self.mover_spot_util.movimentar_aida(coordenada,
                                                     verficar_se_movimentou=True,
                                                     movimentacao_proxima=True,
                                                     limpar_spot_se_necessario=True)

                resultados = testeautopk.listar_nomes_e_coords_por_padrao(self.pointer.pm)

                if len(resultados) == 0:
                    continue

                char_proximos = testeautopk.ordenar_proximos(self.pointer, resultados, limite=20)

                for i, d in enumerate(char_proximos, 100):
                    nome = d.get("nome", "")
                    x = d.get("x", "")
                    y = d.get("y", "")
                    if self.pointer.get_nome_char() == nome or nome in ['Death Tree', 'Forest Orc', 'Death Rider',
                                                                        'Guard Archer']:
                        continue

                    posicionou = self.mover_spot_util.movimentar_aida((y, x), verficar_se_movimentou=True,
                                                                      posicionar_mouse_coordenada=True,
                                                                      limpar_spot_se_necessario=True)

                    if posicionou:
                        print('POSICIONOU!')
                        mouse_util.ativar_click_direito(self.handle)
                        time.sleep(.5)

                        while True:

                            if self.eh_suicide_por_imagem():
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

        # for spot in spots_by_map[mapa]:
        #     self.mover_para(spot)
        #     chars = self.buscar_chars_proximos(spot, raio=...)
        #     if not chars:
        #         continue
        #     for char in chars:
        #         if self.eh_suicide_por_imagem(char):
        #             while self.char_existe(char):
        #                 self.clicar_direito_sobre(char)
        #                 if self.morreu(char):
        #                     break
        #             print("morreu suicide, indo pro proximo spot")
        #         else:
        #             print("não é suicide!")
        #             break
        #
        #         if self.morreu_jogador():
        #             pk = self.ler_pk()
        #             if pk > 1:
        #                 self.limpar_pk()
        #                 return

    def buscar_spot_extra_aida1(self):
        spots = spot_util.buscar_spots_aida_1()
        start = max(0, len(spots) - 3)
        spots_extras = []
        for indice_spot in range(start, len(spots)):
            spots_extras.extend([spots[indice_spot]])
        return spots_extras

    def spots_by_map(self):
        pass

    def mover_para(self):
        pass

    def buscar_chars_proximos(self):
        pass

    def eh_suicide_por_imagem(self):
        screenshot_cm = screenshot_util.capture_window(self.handle)
        eh_suicide = buscar_item_util.buscar_posicoes_item_epecifico('./static/pk/suicide.png',
                                                                     screenshot_cm,
                                                                     confidence_=0.7)
        eh_suiciide = buscar_item_util.buscar_posicoes_item_epecifico('./static/pk/suiciide.png',
                                                                      screenshot_cm,
                                                                      confidence_=0.7)
        return eh_suicide or eh_suiciide

    def char_existe(self):
        pass

    def clicar_direito_sobre(self):
        pass

    def morreu_jogador(self):
        pass

    def _sair_da_safe(self):
        if safe_util.aida(self.handle):
            self.mover_spot_util.movimentar_aida((100, 10), max_tempo=10, movimentacao_proxima=True)  # SAIR DA SAFE

    def _ativar_skil(self):
        if self.classe == 'DL':
            self.teclado_util.selecionar_skill_2()
            mouse_util.clickDireito(self.handle)
            self.teclado_util.selecionar_skill_1()

    def _ativar_pk(self):
        if self.pointer.get_pk_ativo() == 0:
            self.teclado_util.combo_tecla("LCTRL", "LSHIFT")

    def _desativar_pk(self):
        if self.pointer.get_pk_ativo() == 1:
            self.teclado_util.combo_tecla("LCTRL", "LSHIFT")
