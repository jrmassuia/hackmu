import time

import win32gui

from utils import mouse_util
from utils.buscar_item_util import BuscarItemUtil
from utils.teclado_util import Teclado_util


def main():
    window_title = "[1/3] MUCABRASIL"
    handle = find_window_handle_by_partial_title(window_title)

    mouse_util.left_clique(handle, 750, 550)  # clica para abrir email
    mouse_util.left_clique(handle, 600, 365)  # clina na aba mensagens

    caminho_arquivo = "nomes.txt"
    nomes = ler_nomes_do_arquivo(caminho_arquivo)

    titulo = 'ToHeLL Recruta Sala 7 KNV!!!'
    corpo = 'É ativo ou voltou a jogar?\n'
    corpo = corpo + 'Estamos recrutando jogadores ativos para nossa guild,\n'
    corpo = corpo + 'e juntos vamos fortalecer a Sala 7!\n\n'
    corpo = corpo + 'Na ToHeLL, você terá:\n'
    corpo = corpo + 'Discord, PK, BP, UP, Boss, Eventos, CS, Tretas!\n\n'
    corpo = corpo + 'Passe seu WhatsApp que entraremos em contato ou fale com o GM pelo: 67 99615 1861\n\n'
    corpo = corpo + 'Acesse e faça seu cadastro: https://www.tohellguild.com.br\n\n'
    corpo = corpo + 'Venha para a ToHeLL, e faça parte dessa família!'

    # titulo = "AVISO REESTRUTURAÇÃO DA ToHeLL5"
    # corpo = "A ToHeLL5 passará por uma reestruturação completa e será recriada nos próximos dias.n\n\n"
    # corpo = corpo + 'ATENÇÃO: Procure URGENTE um dos outros GMs da ToHeLL para garantir sua vaga em outra guild antes da reformulação.\n\n'
    # corpo = corpo + 'Em caso de dúvidas, fale comigo no WhatsApp: (67) 99674-3107\n\n'

    qtd = 0
    teclado = Teclado_util()
    for nome in nomes:
        mouse_util.left_clique(handle, 510, 520)  # clica no escrever
        teclado.digitar_texto_email(nome.replace(" ", ""), titulo, corpo)
        mouse_util.left_clique(handle, 170, 370)  # clica no botao enviar
        time.sleep(.2)
        achou = BuscarItemUtil(handle).buscar_item_simples('botaook.png')
        if achou:
            print('Player não enviado: ' + nome)
            x, y = achou
            if x and y:
                mouse_util.left_clique(handle, x, y)
                mouse_util.left_clique(handle, 230, 373)  # clina no botao fechar
                mouse_util.left_clique(handle, 50, 500)  # clina no bota sim
        else:
            print('Player enviado: ' + nome)

        qtd = qtd + 1
        # if qtd == 20:
        #     qtd = 0
        #     time.sleep(2)

    print('Quantidade mensagem enviada: ' + str(qtd))


def ler_nomes_do_arquivo(caminho_arquivo):
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
            nomes = [linha.strip() for linha in arquivo if linha.strip()]
        return nomes
    except FileNotFoundError:
        print(f"Erro: O arquivo {caminho_arquivo} não foi encontrado.")
        return []
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")
        return []


def find_window_handle_by_partial_title(partial_title):
    def enum_windows_callback(hwnd, handles):
        if partial_title in win32gui.GetWindowText(hwnd):
            handles.append(hwnd)

    handles = []
    win32gui.EnumWindows(enum_windows_callback, handles)
    return handles[0] if handles else None


if __name__ == "__main__":
    main()
