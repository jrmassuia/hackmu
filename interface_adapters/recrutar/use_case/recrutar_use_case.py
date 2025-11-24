import time
from datetime import datetime

from services.alterar_char_sala_service import AlterarCharSalaService
from services.buscar_personagem_proximo_service import BuscarPersoangemProximoService
from services.verificador_imagem_userbar import VerificadorImagemUseBar
from utils import spot_util, mouse_util
from utils.buscar_item_util import BuscarItemUtil
from utils.json_file_manager_util import JsonFileManager
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers
from utils.teclado_util import Teclado_util


class RecrutarUseCase:
    COOLDOWN_DIAS = 7

    def __init__(self, handle):
        self.handle = handle
        self.pointer = Pointers(handle)
        self.servico_buscar_personagem = BuscarPersoangemProximoService(self.pointer)
        self.teclado = Teclado_util(self.handle)
        self.mover_spot = MoverSpotUtil(self.handle)
        self.verificador_imagem_usebar = VerificadorImagemUseBar()
        self.json = JsonFileManager("./data/recrutamento.json")
        senha = 'is4b3ll20'
        self.alternar_sala = AlterarCharSalaService(self.handle, senha, self.pointer.get_nome_char())

    def execute(self):
        self.mover_sala()

    def mover_sala(self):
        # if 'Narukami' == self.pointer.get_nome_char():
        #     self.movimentar_mapa(self.pointer.get_sala_atual())
        # else:
        salas = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        # salas = [6, 7, 8, 9]
        for sala in salas:
            self.alternar_sala.selecionar_sala(sala)
            self.movimentar_mapa(sala)

    def movimentar_mapa(self, sala):
        self._mover_para_lorencia()
        self._mover_para_atlans()
        self._mover_para_losttower()
        self._mover_para_tk()
        self._mover_para_icarus()
        # self._mover_para_stadium()
        self._mover_para_aida()
        if sala == 1:
            self._mover_para_kanturu()

    def _mover_para_lorencia(self):
        self.teclado.escrever_texto('/move lorencia')
        time.sleep(4)
        self.enviar_carta_personagem_proximo()

    def _mover_para_atlans(self):
        self.teclado.escrever_texto('/move atlans')
        time.sleep(4)
        self.enviar_carta_personagem_proximo()

    def _mover_para_losttower(self):
        self.teclado.escrever_texto('/move losttower')
        time.sleep(4)
        self.enviar_carta_personagem_proximo()

    def _mover_para_tk(self):
        self.teclado.escrever_texto('/move tarkan')
        time.sleep(4)
        self.enviar_carta_personagem_proximo()
        spots = spot_util.buscar_todos_spots_tk()
        self.ir_para_spot(spots)

    def _mover_para_stadium(self):
        self.teclado.escrever_texto('/move stadium')
        spots = spot_util.buscar_todos_spots_tk()
        self.ir_para_spot(spots)

    def _mover_para_icarus(self):
        self.teclado.escrever_texto('/move icarus')
        time.sleep(4)
        spots = spot_util.buscar_spots_icarus(qtd_resets=0)
        self.ir_para_spot(spots)

    def _mover_para_aida(self):
        self.teclado.escrever_texto('/move aida')
        time.sleep(4)
        self.enviar_carta_personagem_proximo()
        spots = spot_util.buscar_todos_spots_aida()
        self.ir_para_spot(spots)

    def _mover_para_kanturu(self):
        self.teclado.escrever_texto('/move kanturu')
        time.sleep(4)
        self.enviar_carta_personagem_proximo()
        spots = spot_util.buscar_spots_k1()
        self.ir_para_spot(spots)

    def ir_para_spot(self, spots):
        for indice_spot, grupo_de_spots in enumerate(spots):
            for grupo in grupo_de_spots:
                classes, coordenadas_spot, coordenada_mouse = grupo

                if 'SM' not in classes:
                    continue

                coordenadas = coordenadas_spot[0]
                movimentou = self._movimentar_char_spot(coordenadas)
                if not movimentou:
                    print('Morreu enquanto procurava player - falha movimentação')
                    return

                self.enviar_carta_personagem_proximo()

    def enviar_carta_personagem_proximo(self):
        resultados = self.servico_buscar_personagem.listar_nomes_e_coords_por_padrao()
        if not resultados:
            return

        proximos = self.servico_buscar_personagem.ordenar_proximos(resultados)
        for registro in proximos:
            nome = registro.get("nome", "")
            if self._verificar_se_esta_sem_guild(nome):
                self._enviar_carta(nome)

    def _movimentar_char_spot(self, coordenadas):
        return self.mover_spot.movimentar(
            coordenadas,
            movimentacao_proxima=True,
            limpar_spot_se_necessario=True)

    def _verificar_se_esta_sem_guild(self, nome):
        return self.verificador_imagem_usebar.verificar_pasta(nome, "./static/usebar/semguild/")

    def _enviar_carta(self, nome):
        if not self.pode_enviar(nome):
            print(f"[RECRUTAMENTO] Carta NÃO enviada para '{nome}': dentro do cooldown de {self.COOLDOWN_DIAS} dias.")
            return False

        mouse_util.left_clique(self.handle, 750, 550)  # clica para abrir email
        mouse_util.left_clique(self.handle, 600, 365)  # clina na aba mensagens

        titulo = 'ToHeLL Recruta Sala 7!!!'
        corpo = 'É ativo ou voltou a jogar?\n'
        corpo = corpo + 'Estamos recrutando jogadores ativos para a ToHeLL, e juntos vamos fortalecer a Sala 7!\n\n'
        corpo = corpo + 'Na ToHeLL, você terá:\n'
        corpo = corpo + 'Sorteios semanais de (VIPs, Itens, Potes)\n'
        corpo = corpo + 'Discord, PK, BP, UP, CS, Tretas!\n\n'
        corpo = corpo + 'Acesse e faça seu cadastro: https://www.tohellguild.com.br e clique em Recrutamento\n'
        corpo = corpo + 'Após o cadastro entraremos em contato, ou envie seu WhatsApp.\n\n'
        corpo = corpo + 'Venha para a ToHeLL e faça parte dessa família!'

        mouse_util.left_clique(self.handle, 510, 520)  # clica no escrever
        self.teclado.digitar_texto_email(nome.replace(" ", ""), titulo, corpo)
        mouse_util.left_clique(self.handle, 170, 370)  # clica no botao enviar
        time.sleep(.2)
        achou = BuscarItemUtil(self.handle).buscar_item_simples('./static/img/botaookcarta.png')
        if achou:
            print('Player não enviado: ' + nome)
            x, y = achou
            if x and y:
                mouse_util.left_clique(self.handle, x, y)
                mouse_util.left_clique(self.handle, 230, 373)  # clina no botao fechar
                mouse_util.left_clique(self.handle, 50, 500)  # clina no bota sim
        else:
            mouse_util.left_clique(self.handle, 786, 339)  # fechar email
            self.registrar_envio(nome)
            print(f"[RECRUTAMENTO] Carta enviada para '{nome}' e registro atualizado.")

    @staticmethod
    def _hoje_iso() -> str:
        return datetime.now().date().isoformat()

    def _carregar(self) -> dict:
        data = self.json.read()
        if not isinstance(data, dict):
            data = {}
        if "jogadores" not in data or not isinstance(data["jogadores"], dict):
            data["jogadores"] = {}
        return data

    def _salvar(self, data: dict) -> None:
        self.json.write(data)

    def pode_enviar(self, nome: str) -> bool:
        data = self._carregar()
        info = data["jogadores"].get(nome)
        if not info:
            return True  # nunca enviado
        try:
            ultimo = datetime.fromisoformat(info.get("ultimo_envio", "1970-01-01")).date()
        except ValueError:
            return True

        hoje = datetime.now().date()
        return (hoje - ultimo).days >= self.COOLDOWN_DIAS

    def registrar_envio(self, nome: str) -> None:
        data = self._carregar()
        jogadores = data["jogadores"]

        info = jogadores.get(nome, {
            "ultimo_envio": "1970-01-01",
            "vezes_enviadas": 0
        })

        info["ultimo_envio"] = self._hoje_iso()
        info["vezes_enviadas"] = int(info.get("vezes_enviadas", 0)) + 1

        jogadores[nome] = info
        self._salvar(data)
