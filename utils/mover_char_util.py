from datetime import datetime

from utils import buscar_coordenada_util, mouse_util


def mover(handle, coord_destino, tempo):
    horaInicio = datetime.now()
    chegouNaCoordenadaDesejada = False

    y_atual, x_atual = buscar_coordenada_util.coordernada()

    if y_atual is None or x_atual is None:
        return False

    y_destino, x_destino = coord_destino

    direcao_x = -1 if x_destino < x_atual else 1  # Determinar a direção ao longo do eixo X
    direcao_y = -1 if y_destino < y_atual else 1  # Determinar a direção ao longo do eixo Y

    coordXanterior = 0
    coordYanterior = 0
    while (x_atual != x_destino) or (y_atual != y_destino):

        ##FALTA FAZER A LOGICA DE DAR A VOLTA NO OBJETO

        # Atualizar as coordenadas atuais

        if y_atual != y_destino:
            if coordYanterior == y_atual:
                clicar_na_posicao(handle, 30, 10)  # direita
                coordYanterior = 0
            elif direcao_y == -1:  # cima
                clicar_na_posicao(handle, -30, 10)
                coordYanterior = y_atual
            elif direcao_y == 1:  # baixo
                clicar_na_posicao(handle, 30, -35)
                coordYanterior = y_atual

        elif x_atual != x_destino:
            if coordXanterior == x_atual:
                clicar_na_posicao(handle, -30, 10)  # cima
                coordXanterior = 0
            if direcao_x == 1:  # direita
                clicar_na_posicao(handle, 30, 10)
                coordXanterior = x_atual
            elif direcao_x == -1:  # esquerda
                clicar_na_posicao(handle, -30, -30)
                coordXanterior = x_atual

        y_atual, x_atual = buscar_coordenada_util.coordernada()

        if y_atual is None or x_atual is None:
            chegouNaCoordenadaDesejada = False
            print('Não encontrou destino Y: ' + str(y_destino) + ' X: ' + str(x_destino))
            break

        # Verificar se chegou ao destino
        if (x_atual == x_destino) and (y_atual == y_destino):
            chegouNaCoordenadaDesejada = True
            break

        if atingiu_tempo_limite(horaInicio, tempo):
            break

    # fecharBauSeEstiverAberto()

    return chegouNaCoordenadaDesejada


def clicar_na_posicao(handle, posx, posy):
    x, y = 400 + posx, 260 - posy  # CENTRO DA TELA
    mouse_util.left_clique(handle, x, y)

def atingiu_tempo_limite(horaIncio, tempo):
    if tempo > 0:
        horaAtual = datetime.now()
        calcTempo = horaAtual - horaIncio
        return calcTempo.seconds > tempo
    return False
