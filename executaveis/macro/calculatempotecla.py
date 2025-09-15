import keyboard
import time

# Lista para armazenar os tempos
tempos_q = []
tempos_entre_q_w = []
tempos_w = []


def registrar_evento(evento):
    """Registra o tempo exato de pressionamento e soltura das teclas."""
    global eventos
    if evento.name in ["q", "w"]:
        eventos.append((evento.name, evento.event_type, time.perf_counter()))


def medir_tempos(max_repeticoes=8):
    """Captura os tempos e calcula estatísticas para macro."""
    global eventos
    eventos = []

    print("Pressione e solte 'Q', depois 'W'. (ESC para sair)\n")

    keyboard.hook(registrar_evento)  # Inicia captura de eventos
    repeticoes = 0

    while repeticoes < max_repeticoes:
        if keyboard.is_pressed("esc"):
            print("\nSaindo...")
            break

        if len(eventos) >= 4:  # Garante que todas as ações foram capturadas
            repeticoes += 1
            dados = {key: None for key in ["q_down", "q_up", "w_down", "w_up"]}

            for tecla, tipo, tempo in eventos:
                if tecla == "q" and tipo == "down":
                    dados["q_down"] = tempo
                elif tecla == "q" and tipo == "up":
                    dados["q_up"] = tempo
                elif tecla == "w" and tipo == "down":
                    dados["w_down"] = tempo
                elif tecla == "w" and tipo == "up":
                    dados["w_up"] = tempo

            if None not in dados.values():
                tempo_q = (dados["q_up"] - dados["q_down"])  # Segurando Q
                tempo_entre_q_w = (dados["w_down"] - dados["q_up"])  # Tempo entre soltar Q e apertar W
                tempo_w = (dados["w_up"] - dados["w_down"])  # Segurando W

                tempos_q.append(tempo_q)
                tempos_entre_q_w.append(tempo_entre_q_w)
                tempos_w.append(tempo_w)

                print(f"\n[{repeticoes}/{max_repeticoes}] Capturado:")
                print(f"   Tempo segurando Q: {tempo_q:.3f} s")
                print(f"   Tempo entre soltar Q e pressionar W: {tempo_entre_q_w:.3f} s")
                print(f"   Tempo segurando W: {tempo_w:.3f} s")

                eventos.clear()  # Limpa para a próxima captura

    keyboard.unhook_all()  # Para de capturar eventos

    if tempos_q:
        tempo_q_medio = sum(tempos_q) / len(tempos_q)
        tempo_entre_q_w_medio = sum(tempos_entre_q_w) / len(tempos_entre_q_w)
        tempo_w_medio = sum(tempos_w) / len(tempos_w)

        print("\n--- Configuração para Macro ---")
        print(f"Tempo médio segurando Q: {tempo_q_medio:.3f} s")
        print(f"Tempo médio entre Q e W: {tempo_entre_q_w_medio:.3f} s")
        print(f"Tempo médio segurando W: {tempo_w_medio:.3f} s")

        return tempo_q_medio, tempo_entre_q_w_medio, tempo_w_medio
    return None, None, None


def executar_macro(tempo_q, tempo_entre_q_w, tempo_w, repeticoes=5):
    """Executa um loop simulando a macro com os tempos médios capturados."""
    print("\nIniciando macro...")
    for i in range(repeticoes):
        print(f"\n[Macro {i + 1}/{repeticoes}]")

        keyboard.press("q")
        time.sleep(tempo_q)
        keyboard.release("q")

        time.sleep(tempo_entre_q_w)  # Intervalo entre Q e W

        keyboard.press("w")
        time.sleep(tempo_w)
        keyboard.release("w")

    print("\nMacro finalizada.")


if __name__ == "__main__":
    tempo_q, tempo_entre_q_w, tempo_w = medir_tempos()

    # if tempo_q and tempo_w:
    #     executar_macro(tempo_q, tempo_entre_q_w, tempo_w)
