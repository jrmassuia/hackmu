# import pydivert
#
# TARGET_IPS = ["104.26.3.210", "172.67.73.4", "104.26.2.210"]
# LOCAL_IP = "127.0.0.1"
# LOCAL_PORT = 443
# SERVER_PORT = 443
#
# filter_str = (
#     f"(tcp.DstPort == {SERVER_PORT} and (ip.DstAddr == {TARGET_IPS[0]} or "
#     f"ip.DstAddr == {TARGET_IPS[1]} or ip.DstAddr == {TARGET_IPS[2]})) or "
#     f"(tcp.SrcPort == {SERVER_PORT} and (ip.SrcAddr == {TARGET_IPS[0]} or "
#     f"ip.SrcAddr == {TARGET_IPS[1]} or ip.SrcAddr == {TARGET_IPS[2]}))"
# )
#
# with pydivert.WinDivert(filter_str) as w:
#     print("[+] Redirecionador ativo.")
#     for packet in w:
#         try:
#             if not packet.payload:
#                 continue
#
#             if packet.is_outbound and packet.dst_addr in TARGET_IPS:
#                 print(f"[→] Redirecionando Client → Server ({packet.dst_addr})")
#                 packet.dst_addr = LOCAL_IP
#                 packet.dst_port = LOCAL_PORT
#
#             elif packet.is_inbound and packet.src_addr in TARGET_IPS:
#                 print(f"[←] Redirecionando Server → Client ({packet.src_addr})")
#                 packet.src_addr = TARGET_IPS[0]
#                 packet.src_port = SERVER_PORT
#
#             w.send(packet)
#
#         except Exception as e:
#             print(f"[ERRO] {e}")
import ipaddress

import pydivert

TARGET_PORT = 443
LOCAL_REDIRECT_IP = "127.0.0.1"

filter_str = f"outbound and tcp.DstPort == {TARGET_PORT}"

with pydivert.WinDivert(filter_str) as w:
    print(f"[+] Redirecionando tráfego de saída na porta {TARGET_PORT} para {LOCAL_REDIRECT_IP}:{TARGET_PORT}")
    for packet in w:
        try:
            # Só manipula pacotes IPv4
            if packet.ipv6 is None:
                packet.dst_addr = LOCAL_REDIRECT_IP
                w.send(packet)
            else:
                # Não manipula IPv6
                w.send(packet)
        except Exception as e:
            print(f"[!] Erro ao redirecionar pacote: {e}")

