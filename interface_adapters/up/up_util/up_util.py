import ctypes
import os
import time

from domain.arduino_teclado import Arduino
from sessao_handle import get_handle_atual
from utils import mouse_util, screenshot_util, limpar_mob_ao_redor_util
from utils.buscar_item_util import BuscarItemUtil
from utils.pointer_util import Pointers
from utils.teclado_util import Teclado_util

usuario32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


class Up_util:

    def __init__(self):
        self.handle = get_handle_atual()
        self.pointer = Pointers()
        self.arduino = Arduino()
        self.teclado_util = Teclado_util()

    def acao_painel_personagem(self, tecla, abrir=True):
        while True:
            self.teclado_util.tap_tecla(tecla)
            time.sleep(.5)
            achou = BuscarItemUtil(self.handle).buscar_posicoes_de_item('./static/img/fechar_painel.png')
            if (abrir and achou) or (abrir is False and achou is None):
                break

    def imagens_sao_iguais(self, img1, img2):
        return screenshot_util.is_image_in_region(img1, img2)

    def selecionar_char_no_launcher(self, char=None):
        folder_path = "./static/up/char"
        mouse_util.tira_mouse_tela(self.handle)
        while True:
            for filename in os.listdir(folder_path):
                if filename.endswith((".png", ".jpg")):

                    if char and char not in filename:
                        continue

                    image_position = self.verifica_se_personagem_esta_na_tela(folder_path, filename)
                    if image_position:
                        x, y = image_position
                        mouse_util.left_clique(self.handle, x, y + 155)
                        mouse_util.left_clique(self.handle, x, y + 155)
                        time.sleep(1)
                        self.clicar_na_imagem_ou_fallback('./static/img/btnconnect.png', None)
                        time.sleep(5)

                        image_position = self.verifica_se_personagem_esta_na_tela(folder_path, filename)
                        if image_position:
                            print('Não achou personagem ao selecionar no launcher: ' + filename)
                            self.selecionar_char_no_launcher()
                        else:
                            print('Achou personagem ao selecionar no launcher: ' + filename)
                            self.teclado_util.selecionar_skill_1()
                            self.teclado_util.pressionar_zoon()
                            return True

    def verifica_se_personagem_esta_na_tela(self, folder_path, filename):
        template_image_path = os.path.join(folder_path, filename)
        screenshot = screenshot_util.capture_window(self.handle)
        image_position = BuscarItemUtil(self.handle).buscar_imagem_na_janela(screenshot,
                                                                             template_image_path,
                                                                             precisao=.80)
        return image_position

    def clicar_na_imagem_ou_fallback(self, imagem_path, fallback_position, timeout=60):
        mouse_util.mover(self.handle, 1, 1)
        start_time = time.time()
        while time.time() - start_time < timeout:
            posicao = BuscarItemUtil(self.handle).buscar_item_simples(imagem_path)
            if posicao:
                mouse_util.left_clique(self.handle, posicao[0], posicao[1])
                return True
            else:
                if fallback_position:
                    mouse_util.mover_click(*fallback_position)
        return False

    def ativar_up_e_centralizar(self):
        mouse_util.ativar_click_direito(self.handle)
        mouse_util.moverCentro(self.handle)

    def ativar_up(self):
        mouse_util.ativar_click_direito(self.handle)

    def desativar_up(self):
        mouse_util.desativar_click_direito(self.handle)

    def clicar_bau(self, x, y):
        if self.arduino.conexao_arduino:
            with self.teclado_util.foco_mutex.focar_mutex():
                self.teclado_util.focus_window()
                self.teclado_util.pressionar_tecla('LALT')
                mouse_util.left_clique(self.handle, x, y)
                self.teclado_util.soltar_tecla('LALT')
        else:
            mouse_util.left_clique(self.handle, x, y)

    def limpar_mob_ao_redor(self, tempo_inicial_limpar_mob_ao_redor, classe):
        if tempo_inicial_limpar_mob_ao_redor is None:
            tempo_inicial_limpar_mob_ao_redor = 999999
        if (time.time() - tempo_inicial_limpar_mob_ao_redor) > 600:
            tempo_inicial_limpar_mob_ao_redor = time.time()
            limpar_mob_ao_redor_util.limpar_mob_ao_redor(self.handle)
            if self.pointer.get_ponto_lvl() > 0:
                if classe == 'DL':
                    if self.pointer.get_reset() >= 250:
                        add = "/v"
                    else:
                        add = "/e"
                elif classe == 'EF':
                    if self.pointer.get_reset() >= 200:
                        add = "/v"
                    else:
                        add = "/a"
                else:
                    add = "/a"

                self.teclado_util.escrever_texto(add + " " + str(self.pointer.get_ponto_lvl()))
        return tempo_inicial_limpar_mob_ao_redor

    def ativar_skill(self, classe, tempo_inicial_ativar_skill):
        if tempo_inicial_ativar_skill == 0 or ((time.time() - tempo_inicial_ativar_skill) > 600):  # 10 mtos
            tempo_inicial_ativar_skill = time.time()
            if classe == 'EF':
                self.teclado_util.selecionar_skill_2()
                mouse_util.clickDireito(self.handle)
                self.teclado_util.selecionar_skill_3()
                mouse_util.clickDireito(self.handle)
                self.teclado_util.selecionar_skill_1()
            elif classe == 'DL':
                self.teclado_util.selecionar_skill_2()
                mouse_util.clickDireito(self.handle)
                self.teclado_util.selecionar_skill_1()
        return tempo_inicial_ativar_skill

    def ativar_desc_item_spot(self):
        if self.pointer.get_mostrar_desc_item() == 0:
            self.teclado_util.tap_alt()

    def enviar_comandos_iniciais(self):
        self.teclado_util.escrever_texto(["/re off", "/autopick on", "/autodc off"])
        self.teclado_util.pressionar_zoon()

    def verificar_nivel_pk(self):

        CAMINHO_PK0 = "./static/pk/pk0.png"
        CAMINHO_PK1 = "./static/pk/pk1.png"
        REGIAO_PK = (350, 270, 80, 25)
        buscar_imagem = BuscarItemUtil(self.handle)

        def _esperar_okinfo() -> bool:
            timeout_s = 5.0
            deadline = time.monotonic() + timeout_s
            while time.monotonic() < deadline:
                mouse_util.mover(self.handle, 1, 1)
                self.teclado_util.escrever_texto("/info")
                time.sleep(0.25)
                if self.pointer.get_situacao_info():
                    return True
            return False

        try:
            if not _esperar_okinfo():
                print("[WARN] /info não apareceu (OKINFO não encontrado dentro do timeout).")
                return None

            time.sleep(.25)

            x, y, w, h = REGIAO_PK
            screenshot = screenshot_util.capture_region(self.handle, x, y, w, h)

            encontrou_pk0 = bool(buscar_imagem.buscar_posicoes_de_item(CAMINHO_PK0, screenshot, precisao=0.90))
            if encontrou_pk0:
                print("[INFO] PK detectado por imagem: 0")
                return 0

            encontrou_pk1 = bool(buscar_imagem.buscar_posicoes_de_item(CAMINHO_PK1, screenshot, precisao=0.90))
            if encontrou_pk1:
                print("[INFO] PK detectado por imagem: 1")
                return 1

            # Se chegou aqui, não reconheceu PK0 nem PK1 na região
            print("[WARN] Não foi possível identificar PK0/PK1 na região. Retornando 100 (desconhecido).")
            return 100

        except Exception as e:
            print(f"[ERRO] verificar_nivel_pk: {e}")
            return None

        finally:
            while True:
                self.teclado_util.tap_esc()
                time.sleep(.25)
                if not self.pointer.get_situacao_info():
                    break
