import json
from datetime import datetime

import win32gui


class SessionManager:
    """
    Responsável por ler e gravar dados da sessão (sessao.json).
    """

    @staticmethod
    def ler_sessao():
        with open("data/sessao.json", "r", encoding="utf-8") as json_file:
            return json.load(json_file)

    @staticmethod
    def gravar_sessao(data):
        with open("data/sessao.json", "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)


class TelaManager:
    """
    Gerencia as operações relacionadas às telas com base no handle.
    """

    @staticmethod
    def alterar_handle(posicao, novo_handle):
        """
        Altera o 'handle' de uma tela com base na posição (índice) fornecida.

        :param posicao: A posição (índice) da tela na lista 'telas'.
        :param novo_handle: O novo valor do 'handle' que será inserido.
        """
        # Carrega os dados da sessão
        data = SessionManager.ler_sessao()

        # Verifica se a posição existe na lista 'telas'
        if posicao < 0 or posicao >= len(data["telas"]):
            print(f"Posição {posicao} inválida. A lista contém {len(data['telas'])} telas.")
            return

        # Atualiza o handle da tela na posição especificada
        data["telas"][posicao]["handle"] = novo_handle

        # Grava a sessão atualizada
        SessionManager.gravar_sessao(data)

    @staticmethod
    def buscar_handle_tela(window_title):
        """
        Busca o handle da janela com base no título da janela.
        """
        handle = win32gui.FindWindow(None, window_title)
        if handle == 0:
            raise ValueError(f"Janela com título '{window_title}' não encontrada")
        return handle

    @staticmethod
    def buscar_tela_por_handle(handle):
        """
        Busca os dados da tela com base no handle.
        """
        data = SessionManager.ler_sessao()
        for tela in data["telas"]:
            if tela.get("handle") == handle:
                return tela
        # print("Tela com handle " + handle + " não encontrada")

    @staticmethod
    def atualizar_tela_por_handle(handle, novo_valor):
        """
        Atualiza os dados da tela com base no handle.
        """
        data = SessionManager.ler_sessao()
        for tela in data["telas"]:
            if tela.get("handle") == handle:
                tela.update(novo_valor)
                SessionManager.gravar_sessao(data)
                return
        raise ValueError(f"Tela com handle {handle} não encontrada")

    @staticmethod
    def adicionar_tela(handle):
        """
        Adiciona uma nova tela ao JSON com o handle especificado.
        """
        data = SessionManager.ler_sessao()
        data["telas"].append({
            "handle": handle
        })
        SessionManager.gravar_sessao(data)


class InventarioManager:
    """
    Responsável por gerenciar ações e dados do inventário.
    """

    @staticmethod
    def atualizar_data_hora_organiza_complex(handle):
        InventarioManager._atualizar_inventario(handle, "dataHoraOrganizaComplex", datetime.now().isoformat())

    @staticmethod
    def atualizar_data_hora_limpar_inventario(handle):
        InventarioManager._atualizar_inventario(handle, "dataHoraLimparInventario", datetime.now().isoformat())

    @staticmethod
    def atualizar_data_hora_guardou_item_no_bau(handle):
        InventarioManager._atualizar_inventario(handle, "dataHoraGuardouItemNoBau", datetime.now().isoformat())

    @staticmethod
    def atualizar_visualizar_inventario(handle, valor):
        InventarioManager._atualizar_inventario(handle, "visualizar", valor)

    @staticmethod
    def buscar_data_hora_organiza_complex(handle):
        return InventarioManager._buscar_inventario_data_hora(handle, "dataHoraOrganizaComplex")

    @staticmethod
    def buscar_data_hora_limpar_inventario(handle):
        return InventarioManager._buscar_inventario_data_hora(handle, "dataHoraLimparInventario")

    @staticmethod
    def buscar_data_hora_guardou_item_no_bau(handle):
        return InventarioManager._buscar_inventario_data_hora(handle, "dataHoraGuardouItemNoBau")

    @staticmethod
    def buscar_visualizacao_inventario(handle):
        tela = TelaManager.buscar_tela_por_handle(handle)
        return tela["inventario"]["visualizar"]

    @staticmethod
    def _atualizar_inventario(handle, campo, valor):
        tela = TelaManager.buscar_tela_por_handle(handle)
        tela["inventario"][campo] = valor
        TelaManager.atualizar_tela_por_handle(handle, tela)

    @staticmethod
    def _buscar_inventario_data_hora(handle, campo):
        tela = TelaManager.buscar_tela_por_handle(handle)
        date_time_str = tela["inventario"][campo]
        return datetime.strptime(date_time_str[0:-1], '%Y-%m-%dT%H:%M:%S.%f')


class BauManager:
    """
    Responsável por gerenciar ações relacionadas ao bau.
    """

    @staticmethod
    def atualizar_para_bau_inicial(handle):
        BauManager._atualizar_bau(handle, "bau 1")

    @staticmethod
    def atualizar_bau(handle, bau):
        BauManager._atualizar_bau(handle, f"bau {bau}")

    @staticmethod
    def buscar_bau_atual(handle):
        tela = TelaManager.buscar_tela_por_handle(handle)
        return tela["bau"]["bauAtual"]

    @staticmethod
    def _atualizar_bau(handle, bau_atual):
        tela = TelaManager.buscar_tela_por_handle(handle)
        tela["bau"]["bauAtual"] = bau_atual
        TelaManager.atualizar_tela_por_handle(handle, tela)


class AutoPickManager:
    """
    Responsável por gerenciar o estado do AutoPick.
    """

    @staticmethod
    def atualizar_autopick_inicial(handle):
        AutoPickManager._atualizar_autopick(handle, "NAO")

    @staticmethod
    def atualizar_autopick_como_iniciado(handle):
        AutoPickManager._atualizar_autopick(handle, "SIM")

    @staticmethod
    def buscar_autopick(handle):
        tela = TelaManager.buscar_tela_por_handle(handle)
        return tela["autopick"]["inciouAutopick"]

    @staticmethod
    def buscar_autopick_zen(handle):
        tela = TelaManager.buscar_tela_por_handle(handle)
        return tela["zen"]["pega"]

    @staticmethod
    def _atualizar_autopick(handle, valor):
        tela = TelaManager.buscar_tela_por_handle(handle)
        tela["autopick"]["inciouAutopick"] = valor
        TelaManager.atualizar_tela_por_handle(handle, tela)


class UpManager:
    """
    Responsável por gerenciar o estado da tecla F8.
    """

    @staticmethod
    def desativar_f8(handle):
        UpManager._atualizar_f8(handle, "NAO")

    @staticmethod
    def ativar_f8(handle):
        UpManager._atualizar_f8(handle, "SIM")

    @staticmethod
    def verifica_se_f8_ativado(handle):
        tela = TelaManager.buscar_tela_por_handle(handle)
        return tela["up"]["F8Pressionado"] == 'SIM'

    @staticmethod
    def _atualizar_f8(handle, valor):
        tela = TelaManager.buscar_tela_por_handle(handle)
        tela["up"]["F8Pressionado"] = valor
        TelaManager.atualizar_tela_por_handle(handle, tela)


class MenuManager:

    @staticmethod
    def buscar_autopick(handle):
        tela = TelaManager.buscar_tela_por_handle(handle)
        return tela["menu"]["autopick"]

    @staticmethod
    def buscar_sd(handle):
        tela = TelaManager.buscar_tela_por_handle(handle)
        return tela["menu"]["sd"]

    @staticmethod
    def buscar_refining(handle):
        tela = TelaManager.buscar_tela_por_handle(handle)
        return tela["menu"]["refining"]

    @staticmethod
    def buscar_upar(handle):
        tela = TelaManager.buscar_tela_por_handle(handle)
        return tela["menu"]["upar"]

    @staticmethod
    def buscar_ativo(handle):
        tela = TelaManager.buscar_tela_por_handle(handle)
        return tela["menu"]["ativo"]

    @staticmethod
    def buscar_todos_itens(handle):
        tela = TelaManager.buscar_tela_por_handle(handle)
        return tela["menu"]["todos_itens"]

    @staticmethod
    def buscar_todas_joias(handle):
        tela = TelaManager.buscar_tela_por_handle(handle)
        return tela["menu"]["joias"]

    @staticmethod
    def buscar_k1(handle):
        tela = TelaManager.buscar_tela_por_handle(handle)
        return tela["menu"]["k1"]

    @staticmethod
    def buscar_k3(handle):
        tela = TelaManager.buscar_tela_por_handle(handle)
        return tela["menu"]["k3"]

    @staticmethod
    def _atualizar_menu(handle, campo, valor):
        tela = TelaManager.buscar_tela_por_handle(handle)
        tela["menu"][campo] = valor
        TelaManager.atualizar_tela_por_handle(handle, tela)


class CoordenadaManager:

    @staticmethod
    def buscar_coordenada(handle):
        return CoordenadaManager.buscar_coody(handle), CoordenadaManager.buscar_coodx(handle)

    @staticmethod
    def buscar_coody(handle):
        tela = TelaManager.buscar_tela_por_handle(handle)
        return tela["coordenada"]["coody"]

    @staticmethod
    def buscar_coodx(handle):
        tela = TelaManager.buscar_tela_por_handle(handle)
        return tela["coordenada"]["coodx"]

    @staticmethod
    def atualizar_coordenada(handle, coody, coodx):
        tela = TelaManager.buscar_tela_por_handle(handle)
        tela["coordenada"]["coody"] = coody
        TelaManager.atualizar_tela_por_handle(handle, tela)

        tela["coordenada"]["coodx"] = coodx
        TelaManager.atualizar_tela_por_handle(handle, tela)
