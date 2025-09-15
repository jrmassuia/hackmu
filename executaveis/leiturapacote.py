import pydivert
import psutil

# Função para encontrar o PID do processo específico
def find_process_pid(process_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'].lower() == process_name.lower():
            return proc.info['pid']
    return None

# Função para encontrar conexões ativas de um processo
def get_connections_by_pid(pid):
    connections = []
    for conn in psutil.net_connections(kind="inet"):
        if conn.pid == pid and conn.laddr:
            connections.append(conn)
    return connections

# Parser para pacote C2 12 - AddCharactersToScope
def parse_add_characters_to_scope(payload):
    if len(payload) < 5 or payload[0] != 0xC2 or payload[3] != 0x12:
        return None

    char_count = payload[4]
    offset = 5
    characters = []

    for _ in range(char_count):
        if offset + 22 > len(payload):
            break
        char_id = int.from_bytes(payload[offset:offset+2], 'big')
        x = payload[offset + 2]
        y = payload[offset + 3]
        name = payload[offset + 9:offset + 19].decode('ascii', errors='ignore').strip('\x00 ')
        characters.append({
            "id": char_id,
            "x": x,
            "y": y,
            "name": name
        })
        offset += 22

    return characters

# Parser para pacote C2 13 - AddTransformedCharactersToScopeRef
def parse_add_transformed_characters_to_scope(payload):
    if len(payload) < 5 or payload[0] != 0xC2 or payload[3] != 0x13:
        return None

    count = payload[4]
    offset = 5
    characters = []

    for _ in range(count):
        if offset + 18 > len(payload):
            break
        char_id = int.from_bytes(payload[offset:offset+2], 'big')
        x = payload[offset + 2]
        y = payload[offset + 3]
        direction = payload[offset + 4]
        transformation_type = payload[offset + 5]
        name = payload[offset + 6:offset + 16].decode('ascii', errors='ignore').strip('\x00 ')
        characters.append({
            "id": char_id,
            "x": x,
            "y": y,
            "direction": direction,
            "transformation_type": transformation_type,
            "name": name
        })
        offset += 18

    return characters

# Nome do processo que você deseja monitorar
process_name = "mucabrasil.exe"
pid = find_process_pid(process_name)

if pid is None:
    print(f"Processo '{process_name}' não encontrado.")
else:
    print(f"Processo '{process_name}' encontrado com PID: {pid}.")

    connections = get_connections_by_pid(pid)
    if not connections:
        print(f"Nenhuma conexão ativa encontrada para o processo '{process_name}' com PID {pid}.")
    else:
        ports = set(conn.laddr.port for conn in connections if conn.laddr)
        if not ports:
            print("Nenhuma porta válida encontrada para capturar pacotes.")
        else:
            filter_str = " or ".join(f"tcp.DstPort == {port} or tcp.SrcPort == {port}" for port in ports)
            print(f"Capturando pacotes nas portas: {', '.join(map(str, ports))}")
            print(f"Filtro gerado: {filter_str}")

            try:
                with pydivert.WinDivert(filter_str) as w:
                    print("Iniciando a captura de pacotes...")

                    for packet in w:
                        ip_origem = packet.src_addr
                        ip_destino = packet.dst_addr
                        payload = packet.payload

                        if len(payload) > 0:
                            if payload.startswith(b'\xC2') and payload[3] == 0x12:
                                chars = parse_add_characters_to_scope(payload)
                                if chars:
                                    print(">>> [AddCharactersToScope] Personagens visíveis:")
                                    for char in chars:
                                        print(f"ID: {char['id']} - Pos: ({char['x']}, {char['y']}) - Nome: {char['name']}")
                            elif payload.startswith(b'\xC2') and payload[3] == 0x13:
                                transformed = parse_add_transformed_characters_to_scope(payload)
                                if transformed:
                                    print(">>> [AddTransformedCharactersToScope] Transformações visíveis:")
                                    for char in transformed:
                                        print(f"ID: {char['id']} - Pos: ({char['x']}, {char['y']}) - Direção: {char['direction']} - Tipo: {char['transformation_type']} - Nome: {char['name']}")
                            else:
                                print(f"Pacote de {len(payload)} bytes capturado. Não identificado.")

                        w.send(packet)

                    print("Captura de pacotes finalizada.")
            except Exception as e:
                print(f"Ocorreu um erro ao tentar capturar pacotes: {e}")
