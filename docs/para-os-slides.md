# Material para os slides

## Slide 5 — Nossa implementação (algoritmo real)

| Item | O que usamos |
|---|---|
| Linguagem / bibliotecas | Python 3 + Flask · `cryptography` (OpenSSL) · `pyHanko` (assinatura de PDF) |
| Formato | **PAdES**: assinatura embutida no próprio PDF (padrão da ICP-Brasil / Adobe) |
| Função hash | **SHA-256** (resumo de 256 bits = 64 caracteres hex) |
| Assinatura | **RSA-PSS**, chave de **2048 bits**, expoente público 65537 |
| Certificado | **X.509** com a chave pública + nome da instituição, embutido no PDF |
| Chave privada | `chaves/privada.pem` (PKCS#8) — fica só no servidor, nunca sai dele |

Trecho do código (app.py) — cabe no slide:

```python
# ASSINAR: hash SHA-256 + chave PRIVADA (RSA-PSS); assinatura e certificado vão para dentro do PDF
signers.sign_pdf(pdf, PdfSignatureMetadata(md_algorithm="sha256"),
                 signer=ASSINANTE_INSTITUICAO, output=saida)

# VERIFICAR: recalcula o hash, usa a chave PÚBLICA do certificado embutido
# e confere se o certificado é o da instituição (âncora de confiança)
status = validate_pdf_signature(assinatura, ValidationContext(trust_roots=[CERT_CONFIAVEL]))
status.intact   # integridade   → hash recalculado == hash assinado
status.valid    # assinatura    → confere com a chave pública
status.trust_problem_indic is None   # autenticidade → certificado é o da instituição
```

## Fluxo conferido com o código final

Assinatura: PDF → SHA-256 → hash → RSA-PSS com **chave privada** → assinatura + certificado **embutidos no PDF**
Verificação: PDF assinado → extrai assinatura e certificado → recalcula SHA-256 → verifica com a **chave pública** do certificado → confere se o certificado é o da instituição

Para a fala: "não precisa de chave extra" **não** significa que não há chave pública. Ela vem
**dentro do PDF**, no certificado. O sistema só precisa saber **qual certificado é confiável**.

## As três checagens (o que cada cenário da demo prova)

| Cenário | Integridade | Assinatura | Autenticidade | O que prova |
|---|---|---|---|---|
| PDF assinado pela instituição | ✓ | ✓ | ✓ | funcionamento normal (verde) |
| Mesmo PDF com a nota alterada (1 byte) | **✕** | ✓ | ✓ | **integridade**: a alteração é detectada |
| PDF alterado re-assinado pelo **falsificador** | ✓ | ✓ | **✕** | **autenticidade**: sem a chave privada da instituição, não há como forjar |

Frase-chave: "Um hash sozinho o falsificador recalcula. Ele até assina com um certificado que diz
'Universidade Exemplo', mas não consegue usar a chave privada da instituição."

## Números para citar

- `exemplos/declaracao_original.pdf` e `declaracao_adulterada.pdf` diferem em **1 byte** (de 799).
- `adulterar.py` altera **1 byte** do PDF já assinado (7.5 → 9.5) e o hash muda por completo (efeito avalanche).
- Os hashes mudam a cada assinatura (a data da assinatura faz parte do arquivo assinado), então use os que aparecerem na tela.

## Ressalva sobre PKI (para a fala)

Nesta demo o certificado da instituição é **autoassinado** e o sistema de verificação já sabe
que ele é o confiável. Na vida real, quem atesta que o certificado pertence à instituição é uma
**Autoridade Certificadora** (ICP-Brasil); é por isso que o Adobe ou o gov.br reconhecem uma
assinatura oficial. O caso do falsificador mostra exatamente por que isso é necessário:
qualquer um consegue criar um certificado com o nome que quiser.

Curiosidade: o RSA-PSS usa um salt aleatório, então assinar o mesmo PDF duas vezes gera
assinaturas diferentes — e ambas são válidas.

## Prints (docs/prints/)

| Arquivo | Uso sugerido |
|---|---|
| `0-tela-inicial.png` | visão geral da ferramenta |
| `1-assinatura-criada.png` | etapa de assinatura (hash, confirmação, baixar PDF assinado) |
| `2-documento-autentico.png` | resultado válido (verde, três ✓) |
| `3-documento-adulterado.png` | integridade ✕ — hashes diferentes lado a lado |
| `4-falsificador-assina.png` | falsificador assina o PDF alterado com a própria chave |
| `5-falsificador-rejeitado.png` | autenticidade ✕ — hashes iguais, mas certificado não confiável |
| `pdf-original.png` / `pdf-adulterada.png` | os dois PDFs lado a lado — só a nota muda |
