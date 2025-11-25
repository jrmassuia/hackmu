import json
import os
from enum import Enum


# Definindo Enums para cada campo
class InventarioFields(Enum):
    DATA_HORA_ORGANIZA_COMPLEX = "dataHoraOrganizaComplex"
    DATA_HORA_LIMPAR_INVENTARIO = "dataHoraLimparInventario"
    DATA_HORA_GUARDOU_ITEM_NO_BAU = "dataHoraGuardouItemNoBau"
    VISUALIZAR = "visualizar"


class BauFields(Enum):
    BAU_ATUAL = "bauAtual"


class AutopickFields(Enum):
    INICIOU_AUTOPICK = "inciouAutopick"


class UpFields(Enum):
    F8_PRESSIONADO = "F8Pressionado"


class ZenFields(Enum):
    PEGA = "pega"


class MenuFields(Enum):
    AUTOPICK = "autopick"
    SD = "sd"
    UPAR = "upar"
    ATIVO = "ativo"
    JOIAS = "joias"
    LIMPAPK = "limpa_pk"
    PICKKANTURU = "pickKanturu"
    ATLANS = 'atlans'
    SD_SMALL = "sd_small"
    SD_MEDIA = "sd_media"
    REF_GEM = "ref_gem"
    REF_PEQ = "ref_peq"
    BUF = "buf"
    PKLIZAR = "pk"
    RECRUTAR = "recrutar"


class GenericoFields(Enum):
    HANDLEDIALOGO = "handledialogo"
    CLASSE_PERSONAGEM = "classe_personagem"


class Generico:
    def __init__(self, data):
        self.data = data

    def atualizar(self, campo, valor):
        if isinstance(campo, Enum):  # Verifica se é um Enum
            campo = campo.value
        self.data[campo] = valor

    def ler(self, campo):
        if isinstance(campo, Enum):  # Verifica se é um Enum
            campo = campo.value
        return self.data.get(campo, None)


# Definindo classes para cada seção do JSON
class Inventario:
    def __init__(self, data):
        self.data = data

    def atualizar(self, campo, valor):
        self.data[campo] = valor

    def ler(self, campo):
        return self.data.get(campo, None)


class Bau:
    def __init__(self, data):
        self.data = data

    def atualizar(self, campo, valor):
        self.data[campo] = valor

    def ler(self, campo):
        return self.data.get(campo, None)


class Autopick:
    def __init__(self, data):
        self.data = data

    def atualizar(self, campo, valor):
        self.data[campo] = valor

    def ler(self, campo):
        return self.data.get(campo, None)


class Up:
    def __init__(self, data):
        self.data = data

    def atualizar(self, campo, valor):
        self.data[campo] = valor

    def ler(self, campo):
        return self.data.get(campo, None)


class Zen:
    def __init__(self, data):
        self.data = data

    def atualizar(self, campo, valor):
        self.data[campo] = valor

    def ler(self, campo):
        return self.data.get(campo, None)


class MenuSessao:
    def __init__(self, data):
        self.data = data

    def atualizar(self, campo, valor):
        self.data[campo] = valor

    def ler(self, campo):
        return self.data.get(campo, None)


# Classe principal Tela
class Sessao:
    def __init__(self, handle, data_folder="./data"):
        self.handle = handle
        self.data_folder = data_folder
        self.file_path = os.path.join(data_folder, f"tela_{handle}.json")

        # Carregar ou criar arquivo JSON
        self.data = self.carregar_ou_criar_arquivo()

        # Inicializando as seções
        self.inventario = Inventario(self.data.get("inventario", {}))
        self.bau = Bau(self.data.get("bau", {}))
        self.autopick = Autopick(self.data.get("autopick", {}))
        self.up = Up(self.data.get("up", {}))
        self.zen = Zen(self.data.get("zen", {}))
        self.menu = MenuSessao(self.data.get("menu", {}))
        self.generico = Generico(self.data.get("generico", {}))

    def carregar_ou_criar_arquivo(self):
        # Verifica se o arquivo existe; caso contrário, cria um novo JSON
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as file:
                return json.load(file)
        else:
            data = {
                "handle": self.handle,
                "generico": {},
                "inventario": {},
                "bau": {},
                "autopick": {},
                "up": {},
                "zen": {},
                "menu": {}
            }
            self.salvar_json(data)
            return data

    def salvar_json(self, data=None):
        if data is None:
            data = {
                "handle": self.handle,
                "generico": self.generico.data,
                "inventario": self.inventario.data,
                "bau": self.bau.data,
                "autopick": self.autopick.data,
                "up": self.up.data,
                "zen": self.zen.data,
                "menu": self.menu.data
            }
        os.makedirs(self.data_folder, exist_ok=True)
        with open(self.file_path, 'w') as file:
            json.dump(data, file, indent=4)

    def atualizar_inventario(self, campo, valor):
        self.inventario.atualizar(campo.value, valor)
        self.salvar_json()

    def atualizar_bau(self, campo, valor):
        self.bau.atualizar(campo.value, valor)
        self.salvar_json()

    def atualizar_autopick(self, campo, valor):
        self.autopick.atualizar(campo.value, valor)
        self.salvar_json()

    def atualizar_up(self, campo, valor):
        self.up.atualizar(campo.value, valor)
        self.salvar_json()

    def atualizar_zen(self, campo, valor):
        self.zen.atualizar(campo.value, valor)
        self.salvar_json()

    def atualizar_menu(self, campo, valor):
        # self.menu.atualizar(campo.value, valor)
        self.menu.atualizar(campo, valor)
        self.salvar_json()

    def atualizar_generico(self, campo, valor):
        self.generico.atualizar(campo, valor)
        self.salvar_json()

    def ler_inventario(self, campo):
        return self.inventario.ler(campo.value)

    def ler_bau(self, campo):
        return self.bau.ler(campo.value)

    def ler_autopick(self, campo):
        return self.autopick.ler(campo.value)

    def ler_zen(self, campo):
        return self.zen.ler(campo.value)

    def ler_up(self, campo):
        return self.up.ler(campo.value)

    def ler_menu(self, campo):
        return self.menu.ler(campo.value)

    def ler_generico(self, campo):
        return self.generico.ler(campo.value)

    @staticmethod
    def limpar_sessao(data_folder="./data"):
        # Exclui todos os arquivos JSON que começam com "tela" na pasta data_folder
        for filename in os.listdir(data_folder):
            if filename.startswith("tela") and filename.endswith(".json"):
                os.remove(os.path.join(data_folder, filename))
