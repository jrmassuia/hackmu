import time

from utils.json_file_manager_util import JsonFileManager


class FocoFilaTelaService:
    FOCO_ATIVO = "ATIVO"
    FOCO_INATIVO = "INATIVO"

    def __init__(self):
        self.json = JsonFileManager("./data/config.json")

    def _alterar_foco(self, novo_foco: str):
        data = self.json.read()
        data["foco"] = novo_foco
        self.json.write(data)

    def _ler_foco(self) -> str:
        return self.json.read().get("foco")

    def ativar_foco(self):
        while True:
            if self.foco_esta_ativo():
                time.sleep(0.5)
            else:
                self._alterar_foco(self.FOCO_ATIVO)
                break

    def inativar_foco(self):
        self._alterar_foco(self.FOCO_INATIVO)

    def foco_esta_ativo(self) -> bool:
        return self._ler_foco() == self.FOCO_ATIVO

    def foco_esta_inativo(self) -> bool:
        return self._ler_foco() == self.FOCO_INATIVO
