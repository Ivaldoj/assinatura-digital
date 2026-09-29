"""
Demonstração acadêmica: Assinatura Digital de PDF e Verificação de Autenticidade.

Como na vida real (gov.br, Adobe, ICP-Brasil), a assinatura fica DENTRO do PDF (padrão PAdES),
junto com o CERTIFICADO da instituição (= chave pública + identidade de quem assinou).

Algoritmo: RSA-PSS (2048 bits) sobre o hash SHA-256 do documento.
Bibliotecas: `cryptography` (chaves e certificado) e `pyHanko` (assinatura PAdES).
Nenhum algoritmo criptográfico é implementado à mão.
"""
import base64
import datetime as dt
import io
import logging
from pathlib import Path

from asn1crypto import keys as asn1_keys, x509 as asn1_x509
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from flask import Flask, jsonify, render_template, request
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign import signers, validation
from pyhanko.sign.general import find_unique_cms_attribute
from pyhanko.sign.validation.status import SignatureCoverageLevel
from pyhanko_certvalidator import ValidationContext
from pyhanko_certvalidator.registry import SimpleCertificateStore

logging.getLogger("pyhanko").setLevel(logging.CRITICAL)            # evita logs técnicos no terminal
logging.getLogger("pyhanko_certvalidator").setLevel(logging.CRITICAL)

KEYS_DIR = Path(__file__).parent / "chaves"
PRIVATE_KEY_FILE = KEYS_DIR / "privada.pem"
CERT_FILE = KEYS_DIR / "certificado.pem"
NOME_INSTITUICAO = "Universidade Exemplo - Emissao de Documentos"


def gerar_certificado(chave, nome):
    """Certificado X.509 autoassinado: liga a CHAVE PÚBLICA a um NOME.
    Na vida real ele seria emitido por uma Autoridade Certificadora (ex.: ICP-Brasil)."""
    titular = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, nome),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Universidade Exemplo"),
    ])
    agora = dt.datetime.now(dt.timezone.utc)
    return (
        x509.CertificateBuilder()
        .subject_name(titular).issuer_name(titular)
        .public_key(chave.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(agora - dt.timedelta(days=1))
        .not_valid_after(agora + dt.timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(x509.KeyUsage(
            digital_signature=True, content_commitment=True, key_cert_sign=True,
            key_encipherment=False, data_encipherment=False, key_agreement=False,
            crl_sign=False, encipher_only=False, decipher_only=False), critical=True)
        .sign(chave, hashes.SHA256())
    )


def carregar_ou_gerar_instituicao():
    """Gera a chave privada e o certificado da instituição na primeira execução."""
    KEYS_DIR.mkdir(exist_ok=True)
    if not PRIVATE_KEY_FILE.exists():
        chave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        PRIVATE_KEY_FILE.write_bytes(chave.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    chave = serialization.load_pem_private_key(PRIVATE_KEY_FILE.read_bytes(), password=None)
    if not CERT_FILE.exists():
        CERT_FILE.write_bytes(gerar_certificado(chave, NOME_INSTITUICAO).public_bytes(serialization.Encoding.PEM))
    return chave, x509.load_pem_x509_certificate(CERT_FILE.read_bytes())


def criar_assinante(chave, certificado):
    """Converte chave e certificado para o formato do pyHanko. prefer_pss=True -> RSA-PSS."""
    chave_der = chave.private_bytes(
        serialization.Encoding.DER, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    return signers.SimpleSigner(
        signing_cert=asn1_x509.Certificate.load(certificado.public_bytes(serialization.Encoding.DER)),
        signing_key=asn1_keys.PrivateKeyInfo.load(chave_der),
        cert_registry=SimpleCertificateStore(),
        prefer_pss=True,
    )


CHAVE_INSTITUICAO, CERT_INSTITUICAO = carregar_ou_gerar_instituicao()
ASSINANTE_INSTITUICAO = criar_assinante(CHAVE_INSTITUICAO, CERT_INSTITUICAO)

# FALSIFICADOR: tem uma chave privada própria e um certificado com o MESMO NOME da instituição.
# Ele consegue assinar, mas o certificado dele não é o certificado confiável da instituição.
_chave_falsa = rsa.generate_private_key(public_exponent=65537, key_size=2048)
ASSINANTE_FALSIFICADOR = criar_assinante(_chave_falsa, gerar_certificado(_chave_falsa, NOME_INSTITUICAO))

# Quem verifica confia SOMENTE no certificado da instituição (a "âncora de confiança").
CERT_CONFIAVEL = asn1_x509.Certificate.load(CERT_INSTITUICAO.public_bytes(serialization.Encoding.DER))

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html", titular=CERT_INSTITUICAO.subject.rfc4514_string(),
                           certificado=CERT_FILE.read_text())


@app.post("/assinar")
def assinar():
    arquivo = request.files["documento"]
    falsificador = request.form.get("assinante") == "falsificador"
    assinante = ASSINANTE_FALSIFICADOR if falsificador else ASSINANTE_INSTITUICAO

    # 1. calcula o SHA-256 do PDF  2. assina o hash com a chave PRIVADA (RSA-PSS)
    # 3. embute assinatura + certificado no próprio PDF (o conteúdo visível não muda)
    saida = io.BytesIO()
    signers.sign_pdf(
        IncrementalPdfFileWriter(io.BytesIO(arquivo.read())),
        signers.PdfSignatureMetadata(field_name="Assinatura", md_algorithm="sha256",
                                     reason="Documento emitido pela Universidade Exemplo"),
        signer=assinante, output=saida,
    )
    pdf_assinado = saida.getvalue()
    assinatura = PdfFileReader(io.BytesIO(pdf_assinado)).embedded_signatures[0]

    return jsonify(
        nome=arquivo.filename.removesuffix(".pdf") + "_assinado.pdf",
        falsificador=falsificador,
        hash=assinatura.compute_digest().hex(),
        pdf=base64.b64encode(pdf_assinado).decode(),
    )


@app.post("/verificar")
def verificar():
    try:
        leitor = PdfFileReader(io.BytesIO(request.files["documento"].read()))
        assinaturas = leitor.embedded_signatures
    except Exception:
        return jsonify(assinado=False, valido=False, erro="O arquivo não é um PDF válido.")
    if not assinaturas:
        return jsonify(assinado=False, valido=False, erro="Nenhuma assinatura digital encontrada neste PDF.")

    assinatura = assinaturas[0]
    # A verificação usa a chave PÚBLICA contida no certificado embutido no PDF
    # e confere se esse certificado é o da instituição (âncora de confiança).
    status = validation.validate_pdf_signature(assinatura, ValidationContext(trust_roots=[CERT_CONFIAVEL]))

    hash_assinado = find_unique_cms_attribute(assinatura.signer_info["signed_attrs"], "message_digest").native
    integro = status.intact and status.coverage == SignatureCoverageLevel.ENTIRE_FILE
    confiavel = status.trust_problem_indic is None

    return jsonify(
        assinado=True,
        valido=integro and status.valid and confiavel,
        integro=integro,                  # hash recalculado == hash que foi assinado
        assinatura_ok=status.valid,       # a conta com a chave pública do certificado fecha
        confiavel=confiavel,              # o certificado é o da instituição
        titular=status.signing_cert.subject.native["common_name"],
        data=status.signer_reported_dt.astimezone().strftime("%d/%m/%Y %H:%M") if status.signer_reported_dt else "-",
        algoritmo=f"{status.pkcs7_signature_mechanism.upper()} + {status.md_algorithm.upper()}",
        hash_assinado=hash_assinado.hex(),
        hash_atual=assinatura.compute_digest().hex(),
    )


if __name__ == "__main__":
    app.run(debug=False, port=5000)
