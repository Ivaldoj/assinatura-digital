# Assinatura Digital e Verificação de Autenticidade de Documentos

Demonstração acadêmica (seminário de Segurança/Criptografia).

## 1. Objetivo

Mostrar, na prática, como uma instituição pode **assinar digitalmente** um documento (certificado,
declaração, comprovante) e como qualquer pessoa pode **verificar** que ele é autêntico e não foi alterado.

Como na vida real (gov.br, Adobe, ICP-Brasil), a assinatura fica **dentro do próprio PDF**. Para
verificar, basta enviar o PDF: não é preciso nenhum arquivo ou chave extra.

O documento **não é cifrado**: ele continua legível. A criptografia aqui não serve para
*confidencialidade* (esconder o conteúdo), e sim para garantir:

- **Integridade**: qualquer alteração, mesmo de 1 byte, é detectada;
- **Autenticidade**: só quem tem a chave privada da instituição consegue produzir uma assinatura aceita.

| | Criptografia para confidencialidade | Assinatura digital |
|---|---|---|
| Objetivo | esconder o conteúdo | provar origem e integridade |
| Quem usa a chave **pública** | quem *cifra* | quem *verifica* |
| Quem usa a chave **privada** | quem *decifra* | quem *assina* |
| O documento fica legível? | não | sim |

## 2. Tecnologia

- **Python 3** + **Flask** (servidor web mínimo, uma página)
- **`cryptography`** (OpenSSL): gera a chave RSA e o certificado X.509
- **`pyHanko`**: assina e verifica PDFs no padrão **PAdES** (o mesmo usado pela ICP-Brasil)

Nenhum algoritmo criptográfico foi implementado manualmente. A chave privada fica só no servidor,
que faz o papel da "instituição"; o navegador nunca tem acesso a ela.

## 3. Técnica criptográfica

- **Hash:** SHA-256
- **Assinatura:** RSA 2048 bits com padding **PSS** (RSA-PSS)
- **Certificado digital (X.509):** "documento" que liga a **chave pública** ao **nome** da instituição.
  Ele vai embutido no PDF assinado; é por isso que a verificação não precisa de chave extra.
- **Arquivos:** `chaves/privada.pem` e `chaves/certificado.pem`, gerados na primeira execução.

> **Simplificação da demo:** o certificado é *autoassinado*. Na vida real ele seria emitido por uma
> **Autoridade Certificadora** (ex.: ICP-Brasil), que atesta que a chave pública é mesmo da instituição.

## 4. Fluxo de assinatura

```
Documento (PDF)
      ↓
   SHA-256
      ↓
    Hash
      ↓
Chave privada  (RSA-PSS)
      ↓
Assinatura digital + certificado  →  embutidos no PDF  (declaracao_assinado.pdf)
```

O conteúdo visível do PDF não muda. O hash cobre o arquivo inteiro, exceto o espaço reservado para a
própria assinatura.

## 5. Fluxo de verificação

```
PDF assinado
      ↓
Extrai assinatura + certificado (chave pública)
      ↓
Recalcula SHA-256 e verifica com a chave pública
      ↓
Três checagens:
  ✓/✕ Integridade     – o hash recalculado é igual ao hash assinado?
  ✓/✕ Assinatura      – a conta com a chave pública do certificado fecha?
  ✓/✕ Autenticidade   – o certificado é o da instituição (confiável)?
      ↓
Documento autêntico ✓  /  adulterado ou assinatura inválida ✕
```

Se um único byte do documento mudar, o SHA-256 muda completamente (efeito avalanche) e a checagem de
**integridade** falha.

**Por que não basta publicar o hash?** Porque um falsificador pode alterar o documento e calcular o
novo hash. Ele pode até assinar com uma chave própria e um certificado **com o mesmo nome** da
instituição, mas esse certificado não é o certificado confiável da instituição, e a checagem de
**autenticidade** falha. A opção "Falsificador" na tela de assinatura demonstra exatamente isso
(a chave dele é gerada em memória a cada execução, apenas para a demo).

## 6. Instalação

```bash
pip install -r requirements.txt
```

## 7. Execução

```bash
python app.py
```

Abra **http://localhost:5000** no navegador.

## 8. Roteiro da demonstração (≈ 3 min 30 s)

Deixe um terminal aberto na pasta do projeto e a pasta de Downloads à mão.

**Parte A: integridade**

1. Aba **ASSINAR**: selecione `exemplos/declaracao_original.pdf`, deixe **Instituição** marcada e clique **Assinar documento**.
2. Mostre o **hash SHA-256** e clique em **Baixar PDF assinado** (`declaracao_original_assinado.pdf`).
3. Aba **VERIFICAR**: envie **só** o PDF assinado → **✓ Documento autêntico** (verde, três checagens ✓).
4. No terminal, o "atacante" muda a nota de 7.5 para 9.5 (1 byte):
   ```bash
   python adulterar.py "<Downloads>/declaracao_original_assinado.pdf"
   ```
5. Verifique `declaracao_original_assinado_adulterado.pdf` → **✕ vermelho**: integridade ✕ e os
   dois hashes aparecem diferentes.

**Parte B: autenticidade ("e se o falsificador assinar de novo?")**

6. Aba **ASSINAR**: selecione `exemplos/declaracao_adulterada.pdf` (nota 9.5), marque **Falsificador** e baixe
   `declaracao_adulterada_assinado_falsificador.pdf`.
7. Verifique esse PDF → **✕ vermelho**: integridade ✓, assinatura ✓, mas **autenticidade ✕**.
   O certificado diz "Universidade Exemplo", porém não é o certificado confiável da instituição.

> Dica: faça um ensaio antes para que a chave e o certificado já estejam gerados. Eles são reutilizados
> entre execuções, então um PDF assinado no ensaio continua válido no dia da apresentação.
> Plano B: deixe os PDFs dos passos 2, 4 e 6 prontos numa pasta.
