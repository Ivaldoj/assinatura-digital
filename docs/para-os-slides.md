# Material para os slides

## Slide 5 — Nossa implementação (algoritmo real)

| Item | O que usamos |
|---|---|
| Linguagem / biblioteca | Python 3 + Flask · biblioteca `cryptography` (OpenSSL) |
| Função hash | **SHA-256** (resumo de 256 bits = 64 caracteres hex) |
| Assinatura | **RSA-PSS**, chave de **2048 bits**, expoente público 65537 |
| Parâmetros do PSS | MGF1 com SHA-256 · salt de tamanho máximo |
| Formato das chaves | `privada.pem` (PKCS#8, fica só no servidor) · `publica.pem` (SubjectPublicKeyInfo) |
| Formato da assinatura | arquivo `.sig` separado, 256 bytes em Base64 — o PDF não é alterado |

Trecho do código (app.py) — cabe no slide:

```python
# ASSINAR (chave privada)
resumo = hashlib.sha256(conteudo).digest()
assinatura = CHAVE_PRIVADA.sign(resumo, PSS, Prehashed(SHA256))

# VERIFICAR (chave pública)
resumo = hashlib.sha256(conteudo).digest()
CHAVE_PUBLICA.verify(assinatura, resumo, PSS, Prehashed(SHA256))
# válido → segue;  inválido → InvalidSignature
```

## Fluxo conferido com o código final

Assinatura: Documento → SHA-256 → hash → RSA-PSS com **chave privada** → `.sig`
Verificação: Documento recebido → SHA-256 (recalculado) → RSA-PSS verify com **chave pública** + `.sig` → válido / inválido

Observação: a verificação não compara dois hashes "à mão"; é a própria operação
`verify` que confirma se a assinatura corresponde ao hash recalculado.

## Números reais para citar (exemplos/)

- `declaracao_original.pdf` (nota 7.5) → `b6f19c8c10d3356a1fb31e80d0f9adeb6fb34b46e935a65072091c3cddddc52f`
- `declaracao_adulterada.pdf` (nota 9.5) → `2ac4618ed57122713fabb17e9ae6c533953f605f93174a67a5163004f50da0ae`
- Os arquivos diferem em **1 byte** (de 799); o hash muda por completo (efeito avalanche).

## Integridade × Autenticidade (o que cada parte da demo prova)

| Cenário | Resultado | O que prova |
|---|---|---|
| Original + assinatura da instituição | ✓ verde | funcionamento normal |
| Adulterado + assinatura original | ✕ vermelho | **integridade**: 1 byte alterado é detectado |
| Adulterado + assinatura nova do **falsificador** | ✕ vermelho | **autenticidade**: sem a chave privada da instituição, não há como forjar |

Frase-chave: "Um hash sozinho o falsificador recalcula. A assinatura, ele não consegue refazer,
porque não tem a chave privada da instituição."

## Ressalva sobre PKI (para a fala)

Nesta demo, a chave pública é confiável porque vem do próprio sistema da instituição.
No mundo real, é preciso provar **de quem** é a chave pública: isso é feito por um
**certificado digital** emitido por uma Autoridade Certificadora (PKI / ICP-Brasil),
que liga a chave pública à identidade da instituição. Ficou fora do escopo de propósito.

Curiosidade: o RSA-PSS usa um salt aleatório, então assinar o mesmo PDF duas vezes gera
arquivos `.sig` diferentes — e ambos são válidos.

## Prints (docs/prints/)

| Arquivo | Uso sugerido |
|---|---|
| `0-tela-inicial.png` | visão geral da ferramenta |
| `1-assinatura-criada.png` | etapa de assinatura (nome, hash, confirmação) |
| `2-documento-autentico.png` | resultado válido (verde) |
| `3-documento-adulterado.png` | resultado inválido (vermelho) |
| `4-falsificador-assina.png` | falsificador re-assina o PDF adulterado com a própria chave |
| `5-falsificador-rejeitado.png` | assinatura do falsificador rejeitada (vermelho) |
| `pdf-original.png` / `pdf-adulterada.png` | os dois PDFs lado a lado — só a nota muda |
