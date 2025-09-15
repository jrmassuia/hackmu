
import asyncio
import ssl

REAL_HOST = "route6-charon.mucabrasil.com.br"
REAL_PORT = 443
SERVER_IP = "172.67.73.4"
SERVER_HOSTNAME = "route6-charon.mucabrasil.com.br"

CERT_FILE = "certs/mu.crt"
KEY_FILE = "certs/mu.key"

def parse_add_characters_to_scope(payload):
    if len(payload) < 5 or payload[0] != 0xC2 or payload[3] != 0x12:
        return None
    char_count = payload[4]
    offset = 5
    characters = []
    for _ in range(char_count):
        if offset + 22 > len(payload):
            break
        char_id = int.from_bytes(payload[offset:offset + 2], 'big')
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

def parse_add_transformed_characters_to_scope(payload):
    if len(payload) < 5 or payload[0] != 0xC2 or payload[3] != 0x13:
        return None
    count = payload[4]
    offset = 5
    characters = []
    for _ in range(count):
        if offset + 18 > len(payload):
            break
        char_id = int.from_bytes(payload[offset:offset + 2], 'big')
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

async def handle(client_reader, client_writer):
    peername = client_writer.get_extra_info("peername")
    print(f"[+] Cliente conectou de {peername}")

    try:
        ssl_client_context = ssl.create_default_context()
        ssl_client_context.check_hostname = False
        ssl_client_context.verify_mode = ssl.CERT_NONE

        server_reader, server_writer = await asyncio.open_connection(
            SERVER_IP, REAL_PORT, ssl=ssl_client_context, server_hostname=SERVER_HOSTNAME
        )
        print(f"[+] Conectado ao servidor real {REAL_HOST}:{REAL_PORT}")

        async def client_to_server():
            try:
                while True:
                    data = await client_reader.read(4096)
                    if not data:
                        break
                    server_writer.write(data)
                    await server_writer.drain()
            except:
                pass

        async def server_to_client():
            try:
                while True:
                    data = await server_reader.read(4096)
                    if not data:
                        break

                    if data.startswith(b'\xC2') and data[3] == 0x12:
                        chars = parse_add_characters_to_scope(data)
                        if chars:
                            print(">>> [AddCharactersToScope]")
                            for char in chars:
                                print(f"ID: {char['id']} - Pos: ({char['x']}, {char['y']}) - Nome: {char['name']}")
                    elif data.startswith(b'\xC2') and data[3] == 0x13:
                        transformed = parse_add_transformed_characters_to_scope(data)
                        if transformed:
                            print(">>> [AddTransformedCharactersToScope]")
                            for char in transformed:
                                print(f"ID: {char['id']} - Pos: ({char['x']}, {char['y']}) - Dir: {char['direction']} - Tipo: {char['transformation_type']} - Nome: {char['name']}")
                    else:
                        print(f"[S→C] {len(data)} bytes recebidos")

                    client_writer.write(data)
                    await client_writer.drain()
            except:
                pass

        await asyncio.gather(client_to_server(), server_to_client())

    except Exception as e:
        print(f"[ERRO] Proxy TLS: {e}")

async def main():
    ssl_server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_server_context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    server = await asyncio.start_server(handle, "127.0.0.1", 443, ssl=ssl_server_context)
    print("[MITM] TLS escutando em 127.0.0.1:443")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
