from typing import Dict, Any

MAPA_MENU: Dict[int, Dict[str, Any]] = {}


def obter_menu(handle: int) -> Dict[str, Any]:
    return MAPA_MENU.get(handle, {})


def atualizar_menu(handle: int, menu: Dict[str, Any]) -> None:
    MAPA_MENU[handle] = menu


def remover_menu(handle: int) -> None:
    MAPA_MENU.pop(handle, None)


def limpar_todos_menus() -> None:
    MAPA_MENU.clear()
