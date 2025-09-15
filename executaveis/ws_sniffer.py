import asyncio

import psutil
from mitmproxy.options import Options
from mitmproxy.tools.dump import DumpMaster


def parse_add_characters(payload: bytes):
    if len(payload) < 5 or payload[0] != 0xC2 or payload[3] != 0x12:
        return None

    count = payload[4]
    offset = 5
    chars = []
    for _ in range(count):
        if offset + 22 > len(payload):
            break
        cid = int.from_bytes(payload[offset:offset+2], 'big')
        x, y = payload[offset + 2], payload[offset + 3]
        name = payload[offset + 9:offset + 19].decode('ascii', 'ignore').strip('\x00 ')
        chars.append({"id": cid, "x": x, "y": y, "name": name})
        offset += 22
    return chars


def parse_add_transformed(payload: bytes):
    if len(payload) < 5 or payload[0] != 0xC2 or payload[3] != 0x13:
        return None

    count = payload[4]
    offset = 5
    chars = []
    for _ in range(count):
        if offset + 18 > len(payload):
            break
        cid = int.from_bytes(payload[offset:offset+2], 'big')
        x, y = payload[offset + 2], payload[offset + 3]
        direction = payload[offset + 4]
        transf_type = payload[offset + 5]
        name = payload[offset + 6:offset + 16].decode('ascii', 'ignore').strip('\x00 ')
        chars.append({
            "id": cid,
            "x": x,
            "y": y,
            "direction": direction,
            "transformation_type": transf_type,
            "name": name
        })
        offset += 18
    return chars


class MuSniffer:
    def websocket_message(self, flow):
        data: bytes = flow.messages[-1].content
        if not data or len(data) < 5:
            return

        if data[0] != 0xC2:
            return

        if data[3] == 0x12:
            chars = parse_add_characters(data)
            if chars:
                print("[AddCharactersToScope]")
                for c in chars:
                    print(f"  ID:{c['id']:>4}  ({c['x']:>3},{c['y']:>3})  {c['name']}")
        elif data[3] == 0x13:
            trans = parse_add_transformed(data)
            if trans:
                print("[AddTransformedCharactersToScope]")
                for t in trans:
                    print(
                        f"  ID:{t['id']:>4}  ({t['x']:>3},{t['y']:>3})  Dir:{t['direction']} Tipo:{t['transformation_type']}  {t['name']}"
                    )


def get_mu_process_proxy_port(process_name="mucabrasil.exe"):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'].lower() == process_name.lower():
            pid = proc.info['pid']
            conns = [c for c in psutil.net_connections(kind="inet") if c.pid == pid and c.status == 'ESTABLISHED']
            if conns:
                return conns[0].raddr.port
    return None


async def main():
    # proxy_port = get_mu_process_proxy_port()
    # if not proxy_port:
    #     print("[ERRO] Não foi possível encontrar a porta de conexão ativa do mucabrasil.exe.")
    #     return

    # print(f"[INFO] Porta alvo do MU detectada: {proxy_port}")

    # opts = Options(listen_host="127.0.0.1", listen_port=8080, mode=["regular"])
    opts = Options(listen_host="127.0.0.1", listen_port=8080, mode=["socks5"])
    m = DumpMaster(opts, with_termlog=True, with_dumper=False)
    m.addons.add(MuSniffer())

    try:
        print("=== Mu WSS Sniffer ativo em 127.0.0.1:8080 ===")
        print("Configure o jogo (ou Proxifier) para redirecionar a porta do servidor MU para 127.0.0.1:8080")
        await m.run()
    except KeyboardInterrupt:
        print("Sniffer encerrado.")
    finally:
        await m.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
