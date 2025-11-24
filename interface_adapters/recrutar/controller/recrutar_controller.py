from interface_adapters.recrutar.use_case.recrutar_use_case import RecrutarUseCase


class RecrutarController:

    def __init__(self, handle):
        self.handle = handle

    def execute(self):
        RecrutarUseCase(self.handle).execute()
