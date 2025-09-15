from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
import os

os.makedirs("certs", exist_ok=True)

# === 1. Gerar chave privada da CA ===
ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
with open("certs/ca.key", "wb") as f:
    f.write(ca_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ))

# === 2. Gerar certificado da CA ===
ca_subject = x509.Name([
    x509.NameAttribute(NameOID.COMMON_NAME, u"MuCA Fake CA"),
])
ca_cert = (
    x509.CertificateBuilder()
    .subject_name(ca_subject)
    .issuer_name(ca_subject)
    .public_key(ca_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.utcnow())
    .not_valid_after(datetime.utcnow() + timedelta(days=3650))
    .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
    .sign(ca_key, hashes.SHA256())
)

with open("certs/ca.crt", "wb") as f:
    f.write(ca_cert.public_bytes(serialization.Encoding.PEM))


# === 3. Gerar chave privada do servidor ===
server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
with open("certs/mu.key", "wb") as f:
    f.write(server_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ))

# === 4. Criar CSR do servidor ===
server_csr = (
    x509.CertificateSigningRequestBuilder()
    .subject_name(x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, u"*.mucabrasil.com.br")
    ]))
    .add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("*.mucabrasil.com.br"),
            x509.DNSName("route4-charon.mucabrasil.com.br")
        ]),
        critical=False
    )
    .sign(server_key, hashes.SHA256())
)

# === 5. Assinar CSR com CA para gerar certificado do servidor ===
server_cert = (
    x509.CertificateBuilder()
    .subject_name(server_csr.subject)
    .issuer_name(ca_cert.subject)
    .public_key(server_csr.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.utcnow())
    .not_valid_after(datetime.utcnow() + timedelta(days=3650))
    .add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("*.mucabrasil.com.br"),
            x509.DNSName("route4-charon.mucabrasil.com.br")
        ]),
        critical=False
    )
    .sign(ca_key, hashes.SHA256())
)

with open("certs/mu.crt", "wb") as f:
    f.write(server_cert.public_bytes(serialization.Encoding.PEM))

# === 6. Unir certificado + chave no formato PEM ===
with open("certs/mu.pem", "wb") as f:
    f.write(server_cert.public_bytes(serialization.Encoding.PEM))
    f.write(server_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ))

print("[✔] Certificados gerados com sucesso na pasta ./certs")
