from interface_adapters.controller.BaseController import BaseController
from interface_adapters.recrutar.use_case.recrutar_use_case import RecrutarUseCase


class RecrutarController(BaseController):

    def _prepare(self):
        pass

    def _run(self):
        RecrutarUseCase(self.handle).execute()
