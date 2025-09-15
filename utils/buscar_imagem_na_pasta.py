import os


def buscar(*path_parts, anchor_folder="static"):
    current_dir = os.path.abspath(os.path.dirname(__file__))

    while True:
        potential_anchor = os.path.join(current_dir, anchor_folder)
        if os.path.isdir(potential_anchor):
            break

        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            raise FileNotFoundError(f"Pasta âncora '{anchor_folder}' não encontrada na hierarquia.")
        current_dir = parent_dir

    return os.path.join(potential_anchor, *path_parts)
