import asyncio
import random
import re
import threading
import time

import win32gui

from interface_adapters.bean.BpConfig import BpConfig
from interface_adapters.controller.DiscordBotController import DiscordBotController
from interface_adapters.helpers.session_manager_new import Sessao, GenericoFields
from utils import mouse_util, buscar_coordenada_util, buscar_item_util, screenshot_util, safe_util, \
    acao_menu_util
from utils.json_file_manager_util import JsonFileManager
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers
from utils.teclado_util import Teclado_util


class BufController:
    CLASSE_BK = 'BK'
    CLASSE_SM = 'SM'
    CLASSE_EF = 'EF'

    MAPA_DEVIAS_1 = 'Devias'
    MAPA_DEVIAS_2 = 'Devias2'
    MAPA_DEVIAS_3 = 'Devias3'
    MAPA_DEVIAS_4 = 'Devias4'
    MAPA_DUNGEON_1 = 'Dungeon'
    MAPA_DUNGEON_2 = 'Dungeon2'
    MAPA_DUNGEON_3 = 'Dungeon3'
    MAPA_ATLANS_1 = 'Atlans'
    MAPA_ATLANS_2 = 'Atlans2'
    MAPA_ATLANS_3 = 'Atlans3'
    MAPA_LOSTTOWER_1 = 'LostTower'
    MAPA_LOSTTOWER_2 = 'LostTower2'
    MAPA_LOSTTOWER_3 = 'LostTower3'
    MAPA_LOSTTOWER_4 = 'LostTower4'
    MAPA_LOSTTOWER_5 = 'LostTower5'
    MAPA_LOSTTOWER_6 = 'LostTower6'
    MAPA_LOSTTOWER_7 = 'LostTower7'

    def __init__(self, handle, conexao_arduino):
        self.handle = handle
        self.conexao_arduino = conexao_arduino
        self.tela = win32gui.GetWindowText(self.handle)
        self.sessao = Sessao(self.handle)
        self.classe = self.sessao.ler_generico(GenericoFields.CLASSE_PERSONAGEM)
        self.pointers = Pointers(handle)
        self.teclado_util = Teclado_util(self.handle, self.conexao_arduino)
        self.mover_spot_util = MoverSpotUtil(self.handle)
        self.channel_id_sl_bp = 1272950663466324008
        self.channel_id_sl_terminal = 1397939857443000371
        self.arquivo_json = "./data/autobuf.json"
        self.json_manager = JsonFileManager(self.arquivo_json)
        self.tempo_espera_safe = 900
        self.discord_bot = None
        self.necessario_esperar_na_safe = False
        self.versao_mapa_atual = 0
        self.ultimo_mapa = ''
        self.teste = False

    def execute(self):
        self.teclado_util.escrever_texto("/re off")
        self.selecionar_skill()
        self.start_discord_bot()

        if self.classe != BufController.CLASSE_BK:
            time.sleep(10)
        else:
            self._limpar_mensagens_discord(self.channel_id_sl_terminal, limpar_todas=True)

        while True:
            if self.classe == BufController.CLASSE_BK:
                deve_mover_char_para_bp = self.ultimo_mapa == '' or self._verifica_se_esta_na_safe() or self._deve_mover_bp()
            else:
                estouro_na_safe = self._verificar_se_estouro_esta_na_safe()

                # Verifica se houve mudança de mapa
                versao_atual = self.versao_mapa_atual
                nova_versao = self._ler_versao_mapa()
                houve_mudanca_de_mapa = nova_versao != versao_atual

                # Considera que está na safe se uma das condições for verdadeira
                deve_mover_char_para_bp = estouro_na_safe or houve_mudanca_de_mapa

                # print(f"Estouro na safe: {estouro_na_safe}")
                # print(f"Versão do mapa atual: {versao_atual}, nova versão detectada: {nova_versao}")
                # print(f"Houve mudança de mapa: {houve_mudanca_de_mapa}")
                # print(f"Deve mover char para BP: {deve_mover_char_para_bp}")

            if deve_mover_char_para_bp:
                self._alterar_situacao_estouro_safe(True)
                self._esperar_na_safe_se_necessario()
                self._escolher_mapa()
                self._alterar_situacao_estouro_safe(False)
                self._verificar_se_possui_zen_move()
                moveu = self._mover_bp()
                if moveu is False:
                    continue
                self._notificar_discord_local_bp()
            else:
                self._ativar_skill()

    def start_discord_bot(self):
        self.discord_bot = DiscordBotController(self.classe, json_manager=self.json_manager)
        bot_thread_bp = threading.Thread(target=self.discord_bot.start, daemon=True)
        bot_thread_bp.start()

        inicio = time.time()
        while time.time() - inicio < 20:
            if self.discord_bot.bot.is_ready():
                break
            time.sleep(0.5)

    def _deve_mover_bp(self):
        comando = self._ler_json_comando_discord()
        if comando != '':
            self._limpar_json_comando_discord()
            if 'move' in comando:
                self.necessario_esperar_na_safe = False
                return True
        return False

    # REGRA PARA VERIFICAR SE O ESTOURO ESTA NA BP CASO O SM OU ELFA TENHA MORRIDO PARA QUE VOLTE NOVAMENTE PARA A BP ONDE ESTEJA O BK
    def _verificar_se_estouro_esta_na_safe(self):
        if self.ultimo_mapa != '' and self._verifica_se_esta_na_safe():

            tempo_total_espera = 120
            intervalo_verificacao = 10
            tempo_esperado = 0
            deve_voltar_para_bp = True
            while tempo_esperado < tempo_total_espera:
                segundos_restantes = tempo_total_espera - tempo_esperado
                nome_personagem = self.pointers.get_nome_char()
                print(f"[{nome_personagem}] Verificando se estouro está na safe. "
                      f"Tempo restante: {segundos_restantes} segundos...")

                time.sleep(intervalo_verificacao)
                tempo_esperado += intervalo_verificacao

                if self._ler_estouro_safe():
                    deve_voltar_para_bp = False
                    print(f'[{nome_personagem}] Estouro na safe, aguardando para realizar movimentação!')
                    break

            return deve_voltar_para_bp

        elif self._ler_estouro_safe() is False:
            return False

        # Após o tempo de espera, se ainda não estiver na safe, retorna False
        return False

    def selecionar_skill(self):
        if self.classe != BufController.CLASSE_EF:
            self.teclado_util.selecionar_skill_1()

    def _escolher_mapa(self):
        if self.classe == BufController.CLASSE_BK:
            self.ultimo_mapa, versao_atual = self._ler_dados_mapa()

            while True:
                bp_escolhida = self._montar_base_bp()
                self.salvar_json_mapa(bp_escolhida)
                novo_mapa, nova_versao = self._ler_dados_mapa()

                if self.ultimo_mapa == novo_mapa:
                    print('BK escolheu o mesmo mapa, buscando outro!')
                    continue
                else:
                    self.versao_mapa_atual = nova_versao
                    self.ultimo_mapa = novo_mapa
                    break
        else:
            while True:
                novo_mapa, nova_versao = self._ler_dados_mapa()
                primeira_movimentacao = self.versao_mapa_atual == 0 and nova_versao != 1
                movimentacao_posterior = self.versao_mapa_atual == nova_versao and self._ler_estouro_safe()

                if primeira_movimentacao or movimentacao_posterior:
                    print(f"[{self.pointers.get_nome_char()}] Esperando troca de mapa pelo BK... "
                          f"Versão: {self.versao_mapa_atual} - Mapa: {self.ultimo_mapa}")
                    time.sleep(10)
                    continue
                else:
                    self.versao_mapa_atual = nova_versao
                    self.ultimo_mapa = novo_mapa
                    break

        print(
            f"[{self.pointers.get_nome_char()}] Novo mapa detectado, versão: "
            f"{self.versao_mapa_atual} - {self.ultimo_mapa}")

    def _mover_bp(self):
        try:
            bp = self.carregar_bpconfig_por_classe(self.classe)
            moveu = self._mover_bp_para_mapa(bp)
            if moveu is False:
                return False
            self.selecionar_party_se_for_bk()
            mouse_util.mover(self.handle, bp.mousex, bp.mousey)
        except ValueError as e:
            print(f"ERRO ao mover BP: {e}")
            return False
        return True

    def _mover_bp_para_mapa(self, bp):
        if self.classe == BufController.CLASSE_EF:  # Delay entre telas para o jogo não bugar
            time.sleep(6)
        elif self.classe == BufController.CLASSE_EF:
            time.sleep(4)
        else:
            time.sleep(2)

        self.teclado_util.escrever_texto("/move " + bp.mapa)
        time.sleep(2)

        tempo_max_movimento = 120
        while True:
            movimentou = False
            if BufController.MAPA_DEVIAS_1 in bp.mapa:
                movimentou = self.mover_spot_util.movimentar_devias((bp.coordy, bp.coordx),
                                                                    max_tempo=tempo_max_movimento,
                                                                    verficar_se_movimentou=True,
                                                                    limpar_spot_se_necessario=True)
            elif BufController.MAPA_DUNGEON_1 in bp.mapa:
                movimentou = self.mover_spot_util.movimentar_dungeon((bp.coordy, bp.coordx),
                                                                     max_tempo=tempo_max_movimento,
                                                                     verficar_se_movimentou=True,
                                                                     limpar_spot_se_necessario=True)
            elif BufController.MAPA_ATLANS_1 in bp.mapa:
                movimentou = self.mover_spot_util.movimentar_atlans((bp.coordy, bp.coordx),
                                                                    max_tempo=tempo_max_movimento,
                                                                    verficar_se_movimentou=True,
                                                                    limpar_spot_se_necessario=True)
            elif BufController.MAPA_LOSTTOWER_1 in bp.mapa:
                movimentou = self.mover_spot_util.movimentar_losttower((bp.coordy, bp.coordx),
                                                                       max_tempo=tempo_max_movimento,
                                                                       verficar_se_movimentou=True,
                                                                       limpar_spot_se_necessario=True)

            time.sleep(1)

            if movimentou is False:
                print(f"[{self.pointers.get_nome_char()}] Tentando Movimentar!")
                self._mover_bp_para_mapa(bp)

            elif movimentou and (bp.coordy == self.pointers.get_cood_y() and bp.coordx == self.pointers.get_cood_x()):
                print(f"[{self.pointers.get_nome_char()}] Movimentou!")
                return True

    def selecionar_party_se_for_bk(self):
        if self.classe == BufController.CLASSE_BK:
            while True:
                acao_menu_util.pressionar_painel_comando(self.handle, self.cone)
                time.sleep(.5)

                screenshot_cm = screenshot_util.capture_window(self.handle)
                image_positions = buscar_item_util.buscar_posicoes_item_epecifico('./static/buf/party.png',
                                                                                  screenshot_cm,
                                                                                  confidence_=0.9)
                if image_positions:
                    x = image_positions[0][0]
                    y = image_positions[0][1]
                    mouse_util.left_clique(self.handle, x, y)
                    mouse_util.left_clique(self.handle, x, y)
                    break

    def _ativar_skill(self):
        bp = self.carregar_bpconfig_por_classe(self.classe)
        mouse_util.mover(self.handle, bp.mousex, bp.mousey)

        mouse_util.ativar_click_direito(self.handle)

        if self.classe == BufController.CLASSE_EF:
            self._buf_elfa()
        else:
            time.sleep(.3)

        mouse_util.desativar_click_direito(self.handle)

    def _buf_elfa(self):
        self.teclado_util.selecionar_skill_1()
        time.sleep(.2)
        self.teclado_util.selecionar_skill_2()

    def _verificar_se_possui_zen_move(self):
        notificou_discord = False

        while True:
            if self.pointers.get_zen() >= int(self._ler_json_zen()):
                break
            else:
                if not notificou_discord:
                    notificou_discord = True
                    self._notificar_discord_char_sem_zen()
                    print(f"[{self.pointers.get_nome_char()}] CHAR SEM ZEN!")
                time.sleep(10)

    def _verifica_se_esta_na_safe(self):
        return (safe_util.lorencia(self.handle) or safe_util.devias(self.handle) or
                safe_util.atlans(self.handle) or safe_util.losttower(self.handle) or
                safe_util.noria(self.handle))

    def _esperar_na_safe_se_necessario(self):
        if self.classe != BufController.CLASSE_BK:
            return
        if not self.necessario_esperar_na_safe:
            self.necessario_esperar_na_safe = True
        else:
            self._notificar_discord_bp_morta()

            check_interval = 10
            waited_time = 0

            if self.teste:
                self.tempo_espera_safe = 10

            while waited_time < self.tempo_espera_safe:
                print(f"Aguardando {self.tempo_espera_safe - waited_time} segundos... - " + self.tela)
                time.sleep(check_interval)
                waited_time += check_interval
                if self._deve_mover_bp():
                    print('Tempo espera finalizado por comando Discord!')
                    break

            print("Tempo de espera finalizado. - " + self.tela)

    def _montar_base_bp(self):
        fontes = [
            self._montar_base_bp_devias_2,
            # self._montar_base_bp_devias_4,
            # self._montar_base_bp_dungeon2,
            # self._montar_base_bp_atlans2,
            # self._montar_base_bp_atlans3,
            self._montar_base_bp_losttower2,
            self._montar_base_bp_losttower4,
            self._montar_base_bp_losttower5,
            self._montar_base_bp_losttower6,
            self._montar_base_bp_losttower7
        ]

        subgrupos_possiveis = []

        for fonte in fontes:
            lista = fonte()
            if lista:  # garante que não é None ou vazio
                subgrupo = random.choice(lista)  # escolhe 1 grupo (lista de BpConfig)
                subgrupos_possiveis.append(subgrupo)

        # Agora temos 1 subgrupo de cada fonte. Aleatoriza e escolhe 1 final
        random.shuffle(subgrupos_possiveis)
        grupo_escolhido = random.choice(subgrupos_possiveis)

        return grupo_escolhido  # retorna o grupo linear com BpConfigs


    def _montar_base_bp_dungeon(self):
        pass

    def _montar_base_bp_dungeon2(self):
        base = [
            [BpConfig(BufController.MAPA_DUNGEON_2, BufController.CLASSE_BK, 1, 350000, 238, 108, 224, 212),
             BpConfig(BufController.MAPA_DUNGEON_2, BufController.CLASSE_SM, 1, 350000, 238, 106, 340, 211),
             BpConfig(BufController.MAPA_DUNGEON_2, BufController.CLASSE_EF, 1, 350000, 238, 105, 340, 211)]
        ]
        return base

    def _montar_base_bp_devias_1(self):
        base = [
            [BpConfig(BufController.MAPA_DEVIAS_1, BufController.CLASSE_BK, 1, 200000, 166, 6, 340, 207),
             BpConfig(BufController.MAPA_DEVIAS_1, BufController.CLASSE_SM, 1, 200000, 168, 6, 458, 220),
             BpConfig(BufController.MAPA_DEVIAS_1, BufController.CLASSE_EF, 1, 200000, 166, 6, 458, 220)]
        ]
        return base

    def _montar_base_bp_devias_2(self):
        base = [
            # 1
            [BpConfig(BufController.MAPA_DEVIAS_2, BufController.CLASSE_BK, 1, 250000, 18, 43, 231, 280),
             BpConfig(BufController.MAPA_DEVIAS_2, BufController.CLASSE_SM, 1, 250000, 20, 43, 357, 286),
             BpConfig(BufController.MAPA_DEVIAS_2, BufController.CLASSE_EF, 1, 250000, 22, 43, 357, 286)],
            # 2
            [BpConfig(BufController.MAPA_DEVIAS_2, BufController.CLASSE_BK, 2, 250000, 61, 8, 350, 214),
             BpConfig(BufController.MAPA_DEVIAS_2, BufController.CLASSE_SM, 2, 250000, 63, 8, 466, 218),
             BpConfig(BufController.MAPA_DEVIAS_2, BufController.CLASSE_EF, 2, 250000, 65, 8, 466, 218)],
            # 3
            [BpConfig(BufController.MAPA_DEVIAS_2, BufController.CLASSE_BK, 3, 250000, 7, 52, 311, 297),
             BpConfig(BufController.MAPA_DEVIAS_2, BufController.CLASSE_SM, 3, 250000, 7, 54, 432, 291),
             BpConfig(BufController.MAPA_DEVIAS_2, BufController.CLASSE_EF, 3, 250000, 7, 56, 432, 291)],
            # 4
            [BpConfig(BufController.MAPA_DEVIAS_2, BufController.CLASSE_BK, 3, 250000, 15, 9, 309, 277),
             BpConfig(BufController.MAPA_DEVIAS_2, BufController.CLASSE_SM, 3, 250000, 15, 11, 424, 283),
             BpConfig(BufController.MAPA_DEVIAS_2, BufController.CLASSE_EF, 3, 250000, 15, 13, 424, 283)]
        ]
        return base

    def _montar_base_bp_devias_4(self):
        base = [
            [BpConfig(BufController.MAPA_DEVIAS_4, BufController.CLASSE_BK, 1, 350000, 51, 129, 340, 245),
             BpConfig(BufController.MAPA_DEVIAS_4, BufController.CLASSE_SM, 1, 350000, 53, 129, 458, 239),
             BpConfig(BufController.MAPA_DEVIAS_4, BufController.CLASSE_EF, 1, 350000, 55, 129, 458, 239)]
        ]
        return base

    def _montar_base_bp_atlans(self):
        pass

    def _montar_base_bp_atlans2(self):
        base = [
            # 1
            [BpConfig(BufController.MAPA_ATLANS_2, BufController.CLASSE_BK, 1, 450000, 238, 8, 323, 218),
             BpConfig(BufController.MAPA_ATLANS_2, BufController.CLASSE_SM, 1, 450000, 240, 8, 460, 218),
             BpConfig(BufController.MAPA_ATLANS_2, BufController.CLASSE_EF, 1, 450000, 242, 8, 460, 218)],
            # 2
            [BpConfig(BufController.MAPA_ATLANS_2, BufController.CLASSE_BK, 2, 450000, 214, 22, 236, 264),
             BpConfig(BufController.MAPA_ATLANS_2, BufController.CLASSE_SM, 2, 450000, 216, 22, 347, 281),
             BpConfig(BufController.MAPA_ATLANS_2, BufController.CLASSE_EF, 2, 450000, 218, 22, 347, 281)]
        ]
        return base

    def _montar_base_bp_atlans3(self):
        base = [
            # 1
            [BpConfig(BufController.MAPA_ATLANS_3, BufController.CLASSE_BK, 3, 500000, 78, 114, 330, 227),
             BpConfig(BufController.MAPA_ATLANS_3, BufController.CLASSE_SM, 3, 500000, 80, 114, 446, 240),
             BpConfig(BufController.MAPA_ATLANS_3, BufController.CLASSE_EF, 3, 500000, 82, 114, 446, 240)]
        ]
        return base

    def _montar_base_bp_losttower(self):
        pass

    def _montar_base_bp_losttower2(self):
        base = [
            [BpConfig(BufController.MAPA_LOSTTOWER_2, BufController.CLASSE_BK, 1, 550000, 211, 250, 229, 282),
             BpConfig(BufController.MAPA_LOSTTOWER_2, BufController.CLASSE_SM, 1, 550000, 213, 250, 356, 289),
             BpConfig(BufController.MAPA_LOSTTOWER_2, BufController.CLASSE_EF, 1, 550000, 215, 250, 354, 292)]
        ]
        return base

    # def _montar_base_bp_losttower3(self): METEORO MATA A ELFA
    #     base = [
    #         # 1
    #         [BpConfig(BufController.MAPA_LOSTTOWER_3, BufController.CLASSE_BK, 1, 600000, 80, 203, 309, 289),
    #          BpConfig(BufController.MAPA_LOSTTOWER_3, BufController.CLASSE_SM, 1, 600000, 80, 205, 437, 294),
    #          BpConfig(BufController.MAPA_LOSTTOWER_3, BufController.CLASSE_EF, 1, 600000, 80, 207, 437, 294)],
    #         # 2
    #         [BpConfig(BufController.MAPA_LOSTTOWER_3, BufController.CLASSE_BK, 2, 600000, 82, 250, 252, 279),
    #          BpConfig(BufController.MAPA_LOSTTOWER_3, BufController.CLASSE_SM, 2, 600000, 84, 250, 361, 290),
    #          BpConfig(BufController.MAPA_LOSTTOWER_3, BufController.CLASSE_EF, 2, 600000, 86, 250, 361, 290)],
    #     ]
    #     return base

    def _montar_base_bp_losttower4(self):
        base = [
            # 1
            [BpConfig(BufController.MAPA_LOSTTOWER_4, BufController.CLASSE_BK, 1, 650000, 123, 89, 226, 278),
             BpConfig(BufController.MAPA_LOSTTOWER_4, BufController.CLASSE_SM, 1, 650000, 126, 89, 344, 294),
             BpConfig(BufController.MAPA_LOSTTOWER_4, BufController.CLASSE_EF, 1, 650000, 129, 89, 344, 294)],
            # 2
            [BpConfig(BufController.MAPA_LOSTTOWER_4, BufController.CLASSE_BK, 2, 650000, 133, 86, 244, 220),
             BpConfig(BufController.MAPA_LOSTTOWER_4, BufController.CLASSE_SM, 2, 650000, 133, 88, 358, 233),
             BpConfig(BufController.MAPA_LOSTTOWER_4, BufController.CLASSE_EF, 2, 650000, 133, 90, 358, 233)],
            # 3
            [BpConfig(BufController.MAPA_LOSTTOWER_4, BufController.CLASSE_BK, 3, 650000, 106, 119, 241, 265),
             BpConfig(BufController.MAPA_LOSTTOWER_4, BufController.CLASSE_SM, 3, 650000, 108, 119, 364, 270),
             BpConfig(BufController.MAPA_LOSTTOWER_4, BufController.CLASSE_EF, 3, 650000, 110, 119, 364, 270)]
        ]
        return base

    def _montar_base_bp_losttower5(self):
        base = [
            [BpConfig(BufController.MAPA_LOSTTOWER_5, BufController.CLASSE_BK, 1, 800000, 81, 60, 234, 276),
             BpConfig(BufController.MAPA_LOSTTOWER_5, BufController.CLASSE_SM, 1, 800000, 82, 60, 358, 280),
             BpConfig(BufController.MAPA_LOSTTOWER_5, BufController.CLASSE_EF, 1, 800000, 84, 60, 358, 280)]
        ]
        return base

    def _montar_base_bp_losttower6(self):
        base = [
            # 1
            [BpConfig(BufController.MAPA_LOSTTOWER_6, BufController.CLASSE_BK, 1, 750000, 28, 35, 313, 277),
             BpConfig(BufController.MAPA_LOSTTOWER_6, BufController.CLASSE_SM, 1, 750000, 28, 33, 430, 280),
             BpConfig(BufController.MAPA_LOSTTOWER_6, BufController.CLASSE_EF, 1, 750000, 28, 31, 430, 280)],
            # 2
            [BpConfig(BufController.MAPA_LOSTTOWER_6, BufController.CLASSE_BK, 2, 750000, 11, 52, 307, 281),
             BpConfig(BufController.MAPA_LOSTTOWER_6, BufController.CLASSE_SM, 2, 750000, 11, 50, 433, 281),
             BpConfig(BufController.MAPA_LOSTTOWER_6, BufController.CLASSE_EF, 2, 750000, 11, 48, 433, 281)]
        ]
        return base

    def _montar_base_bp_losttower7(self):
        base = [
            [BpConfig(BufController.MAPA_LOSTTOWER_7, BufController.CLASSE_BK, 1, 800000, 2, 105, 307, 283),
             BpConfig(BufController.MAPA_LOSTTOWER_7, BufController.CLASSE_SM, 1, 800000, 2, 107, 437, 294),
             BpConfig(BufController.MAPA_LOSTTOWER_7, BufController.CLASSE_EF, 1, 800000, 2, 109, 437, 294)]
        ]
        return base

    def _notificar_discord_local_bp(self):
        if self.classe == BufController.CLASSE_BK:
            coordenadas = buscar_coordenada_util.coordernada(self.handle)
            mapa = self._formatar_nome_mapa(self.ultimo_mapa)
            texto = (
                "---\n"
                f"🔸 ***BP ONLINE***\n"
                f"🔸 Mapa: {mapa}\n"
                f"🔸 Coordenadas: ({coordenadas[0]}, {coordenadas[1]})"
            )
            self._enviar_mensagem_discord(self.channel_id_sl_bp, texto)

    def _notificar_discord_char_sem_zen(self):
        texto = (
            "---\n"
            f"🚨️️ **STATUS DO CHAR**\n"
            f"🧙‍ CHAR [{self.pointers.get_nome_char()}] está sem Zen!\n"
            f"💰 Zen atual: {self.pointers.get_zen()}\n"
            f"🛒 É necessário comprar um item da loja pessoal para conseguir mover o personagem."
        )
        self._enviar_mensagem_discord(self.channel_id_sl_terminal, texto)

    def _notificar_discord_bp_morta(self):
        texto = (
            "---\n"
            f"🚨️🚨️🚨️ ***BP MORTA*** 🚨️🚨️🚨️\n"
            f"⏳ Aguardando {self.tempo_espera_safe} segundos para mover para o próximo local."
        )
        self._enviar_mensagem_discord(self.channel_id_sl_terminal, texto, enviar_imagem=False)

    def _enviar_mensagem_discord(self, channel_id, mensagem: str, enviar_imagem=True):
        print('Enviando msg para o Discord!\n' + mensagem)

        if self.teste:
            return

        time.sleep(10)

        imagem = screenshot_util.capture_window(self.handle) if enviar_imagem else None

        if not self.discord_bot.bot.loop.is_running():
            print("O loop do bot ainda não está rodando.")
            return

        self._limpar_mensagens_discord(channel_id)

        envio = self.discord_bot.enviar_mensagem(imagem, mensagem, channel_id)

        asyncio.run_coroutine_threadsafe(envio, self.discord_bot.bot.loop).result()
        time.sleep(2)

    def _limpar_mensagens_discord(self, channel_id, limpar_todas=False):
        if limpar_todas:
            acao = self.discord_bot.limpar_todas_mensagens(channel_id)
        elif channel_id == self.channel_id_sl_bp:
            acao = self.discord_bot.limpar_mensagens(channel_id)
        else:
            acao = self.discord_bot.limpar_mensagens_antigas(channel_id)

        asyncio.run_coroutine_threadsafe(acao, self.discord_bot.bot.loop).result()

    def _formatar_nome_mapa(self, nome_mapa: str) -> str:
        nome_mapa = nome_mapa.upper()
        match = re.match(r"([A-Za-z]+)(\d+)", nome_mapa)
        if match:
            nome, numero = match.groups()
            return f"{nome} {numero}"
        return nome_mapa

    def montar_json_do_grupo(self, grupos):
        if not grupos:
            return {}

        bp0 = grupos[0]
        mapa = bp0.mapa
        localizacao = bp0.localizacao
        zen = bp0.zen

        tipo_classe = []
        for grupo in grupos:
            tipo_classe.append({
                "classe": grupo.classe,
                "coordy": grupo.coordy,
                "coordx": grupo.coordx,
                "mousex": grupo.mousex,
                "mousey": grupo.mousey
            })

        return {
            "mapa": mapa,
            "localizacao": localizacao,
            "versao_mapa": self.versao_mapa_atual + 1,
            "estouro_safe": True,
            "zen": zen,
            "comando_discord": "",
            "tipo_classe": tipo_classe
        }

    def carregar_bpconfig_por_classe(self, classe_desejada: str) -> BpConfig:
        data = self.json_manager.read()

        for item in data.get("tipo_classe", []):
            if item.get("classe") == classe_desejada:
                return BpConfig(
                    mapa=data.get("mapa"),
                    classe=item.get("classe"),
                    localizacao=data.get("localizacao"),
                    zen=data.get("zen"),
                    coordy=item.get("coordy"),
                    coordx=item.get("coordx"),
                    mousex=item.get("mousex"),
                    mousey=item.get("mousey")
                )

        raise ValueError(f"Classe '{classe_desejada}' não encontrada no JSON.")

    def _carregar_json_mapa(self):
        return self.json_manager.read()

    def _ler_json_mapa(self):
        data = self._carregar_json_mapa()
        return data["mapa"]

    def _ler_versao_mapa(self):
        data = self._carregar_json_mapa()
        return data.get("versao_mapa", 0)

    def _ler_json_zen(self):
        data = self._carregar_json_mapa()
        return data["zen"]

    def _ler_json_comando_discord(self):
        data = self._carregar_json_mapa()
        return data["comando_discord"]

    def _ler_dados_mapa(self):
        data = self._carregar_json_mapa()
        return data.get("mapa", ""), data.get("versao_mapa", 0)

    def _ler_estouro_safe(self):
        data = self._carregar_json_mapa()
        return data.get("estouro_safe")

    def salvar_json_mapa(self, grupo):
        data = self.montar_json_do_grupo(grupo)
        self.json_manager.write(data)

    def _alterar_situacao_estouro_safe(self, situacao):
        if self.classe == BufController.CLASSE_BK:
            data = self._carregar_json_mapa()
            data["estouro_safe"] = situacao
            self.json_manager.write(data)

    def _limpar_json_comando_discord(self):
        data = self._carregar_json_mapa()
        data["comando_discord"] = ""
        self.json_manager.write(data)
