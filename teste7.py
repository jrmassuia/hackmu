
import frida
import time

def on_message(message, data):
    if message["type"] == "send":
        print("[DATA]:", message["payload"])
    elif message["type"] == "error":
        print("[ERROR]:", message["stack"])

processo = "mucabrasil.exe"  # Altere se o executável tiver outro nome

session = frida.attach(processo)

script = session.create_script("""
Interceptor.attach(Module.getExportByName("ws2_32.dll", "recv"), {
    onEnter: function (args) {
        this.buf = args[1];
    },
    onLeave: function (retval) {
        if (retval > 0) {
            var data = Memory.readByteArray(this.buf, retval.toInt32());
            var header = Memory.readU8(this.buf);
            var code = Memory.readU8(this.buf.add(3));
            if (header === 0xC2 && (code === 0x12 || code === 0x13)) {
                send(hexdump(data, { offset: 0, length: retval.toInt32(), header: true, ansi: false }));
            }
        }
    }
});
""")
script.on("message", on_message)
script.load()

print("[✓] Hook ativo. Pressione Ctrl+C para sair.")
while True:
    time.sleep(1)
