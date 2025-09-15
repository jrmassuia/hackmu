from flask import Flask, request, jsonify
import clickold


app = Flask(__name__)

@app.route('/process_payload', methods=['POST'])
def process_payload():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Payload inválido"}), 400

    source_ip = data.get("source_ip")
    destination_ip = data.get("destination_ip")
    payload = data.get("payload")

    print(f"Recebido payload de {source_ip} para {destination_ip}: {payload}")
    # Adicione a lógica para manipular o payload aqui

    return jsonify({"message": "Payload processado com sucesso"}), 200

if __name__ == "__main__":
    app.run(debug=True)
