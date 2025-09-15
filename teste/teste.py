import pydivert
import psutil
import requests

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
        if conn.pid == pid and conn.laddr:  # Verifica se há um endereço local válido
            connections.append(conn)
    return connections

# Nome do processo que você deseja monitorar
process_name = "mucabrasil.exe"
pid = find_process_pid(process_name)

if pid is None:
    print(f"Processo '{process_name}' não encontrado.")
else:
    print(f"Processo '{process_name}' encontrado com PID: {pid}.")

    # Verifique conexões ativas do processo
    connections = get_connections_by_pid(pid)
    if not connections:
        print(f"Nenhuma conexão ativa encontrada para o processo '{process_name}' com PID {pid}.")
    else:
        # Lista as portas para construir o filtro
        ports = set(conn.laddr.port for conn in connections if conn.laddr)
        if not ports:
            print("Nenhuma porta válida encontrada para capturar pacotes.")
        else:
            filter_str = " or ".join(f"tcp.DstPort == {port} or tcp.SrcPort == {port}" for port in ports)
            print(f"Capturando pacotes nas portas: {', '.join(map(str, ports))}")
            print(f"Filtro gerado: {filter_str}")

            # Configuração do servidor local
            server_url = "http://127.0.0.1:5000/process_payload"  # Altere para a URL do seu servidor local

            # Inicia a captura de pacotes
            try:
                with pydivert.WinDivert(filter_str) as w:
                    print("Iniciando a captura de pacotes...")

                    for packet in w:
                        ip_origem = packet.src_addr
                        ip_destino = packet.dst_addr
                        payload = packet.payload

                        # Exibe informações básicas do pacote
                        if len(payload) > 0:
                            print(f"Pacote capturado: Origem {ip_origem}, Destino {ip_destino}, Tamanho do Payload: {len(payload)} bytes")
                            print(f"Payload: {payload}")

                            # Envia o payload para o servidor local
                            try:
                                response = requests.post(server_url, json={
                                    "source_ip": ip_origem,
                                    "destination_ip": ip_destino,
                                    "payload": str(payload)  # Envia o payload como uma string hexadecimal
                                })
                                if response.status_code == 200:
                                    print("Payload enviado ao servidor com sucesso.")
                                else:
                                    print(f"Erro ao enviar payload ao servidor: {response.status_code}")
                            except requests.RequestException as e:
                                print(f"Erro ao conectar ao servidor: {e}")

                        # Reenvia o pacote
                        w.send(packet)

                    print("Captura de pacotes finalizada.")
            except Exception as e:
                print(f"Ocorreu um erro ao tentar capturar pacotes: {e}")
