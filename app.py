"""
Demonstração acadêmica: Assinatura Digital e Verificação de Autenticidade.

Algoritmo: RSA-PSS (2048 bits) sobre o hash SHA-256 do documento.
Biblioteca: `cryptography` (Python / OpenSSL). Nenhum algoritmo é implementado à mão.
"""
import base64
import hashlib
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa, utils
from flask import Flask, jsonify, render_template, request

KEYS_DIR = Path(__file__).parent / "chaves"
PRIVATE_KEY_FILE = KEYS_DIR / "privada.pem"
PUBLIC_KEY_FILE = KEYS_DIR / "publica.pem"

# Configuração do RSA-PSS (a mesma na assinatura e na verificação)
PSS = padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH)
PREHASHED_SHA256 = utils.Prehashed(hashes.SHA256())  # "o que vou assinar já é um hash SHA-256"


def carregar_ou_gerar_chaves():
    """Gera o par de chaves da instituição na primeira execução e o reutiliza depois."""
    if not PRIVATE_KEY_FILE.exists():
        KEYS_DIR.mkdir(exist_ok=True)
        chave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        PRIVATE_KEY_FILE.write_bytes(chave.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ))
        PUBLIC_KEY_FILE.write_bytes(chave.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ))
    privada = serialization.load_pem_private_key(PRIVATE_KEY_FILE.read_bytes(), password=None)
    publica = serialization.load_pem_public_key(PUBLIC_KEY_FILE.read_bytes())
    return privada, publica


CHAVE_PRIVADA, CHAVE_PUBLICA = carregar_ou_gerar_chaves()

app = Flask(__name__)


def sha256(conteudo: bytes) -> bytes:
    return hashlib.sha256(conteudo).digest()


@app.get("/")
def index():
    return render_template("index.html", chave_publica=PUBLIC_KEY_FILE.read_text())


@app.post("/assinar")
def assinar():
    arquivo = request.files["documento"]
    conteudo = arquivo.read()                     # o documento NÃO é alterado

    resumo = sha256(conteudo)                     # 1. Documento -> SHA-256 -> hash
    assinatura = CHAVE_PRIVADA.sign(resumo, PSS, PREHASHED_SHA256)  # 2. hash + chave PRIVADA

    return jsonify(
        nome=arquivo.filename,
        hash=resumo.hex(),
        assinatura=base64.b64encode(assinatura).decode(),
    )


@app.post("/verificar")
def verificar():
    conteudo = request.files["documento"].read()
    try:
        assinatura = base64.b64decode(request.files["assinatura"].read(), validate=True)
    except ValueError:
        assinatura = b""                          # arquivo de assinatura corrompido

    resumo = sha256(conteudo)                     # recalcula o hash do documento recebido
    try:
        CHAVE_PUBLICA.verify(assinatura, resumo, PSS, PREHASHED_SHA256)  # só a chave PÚBLICA
        valido = True
    except InvalidSignature:
        valido = False

    return jsonify(valido=valido, hash=resumo.hex())


if __name__ == "__main__":
    app.run(debug=False, port=5000)
