# Assinatura Digital e Verificação de Autenticidade de Documentos

Demonstração acadêmica (seminário de Segurança/Criptografia).

## 1. Objetivo

Mostrar, na prática, como uma instituição pode **assinar digitalmente** um documento (certificado,
declaração, comprovante) e como qualquer pessoa pode **verificar** que ele é autêntico e não foi alterado.

O documento **não é cifrado**: ele continua legível. A criptografia aqui não serve para
*confidencialidade* (esconder o conteúdo), e sim para garantir:

- **Integridade**: qualquer alteração, mesmo de 1 byte, é detectada;
- **Autenticidade**: só quem tem a chave privada da instituição consegue produzir uma assinatura válida.

| | Criptografia para confidencialidade | Assinatura digital |
|---|---|---|
| Objetivo | esconder o conteúdo | provar origem e integridade |
| Quem usa a chave **pública** | quem *cifra* | quem *verifica* |
| Quem usa a chave **privada** | quem *decifra* | quem *assina* |
| O documento fica legível? | não | sim |

## 2. Tecnologia

- **Python 3** + **Flask** (servidor web mínimo, uma página)
- Biblioteca **`cryptography`** (baseada em OpenSSL). Nenhum algoritmo foi implementado manualmente.

A chave privada fica só no servidor, que faz o papel da "instituição". O navegador nunca tem acesso a ela.

## 3. Técnica criptográfica

- **Hash:** SHA-256 (resumo de 256 bits do arquivo)
- **Assinatura:** RSA 2048 bits com padding **PSS** (RSA-PSS), hash SHA-256
- **Chaves:** geradas automaticamente na primeira execução em `chaves/privada.pem` e `chaves/publica.pem`

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
Assinatura digital  →  arquivo  documento.pdf.sig
```

O PDF original não é modificado. A assinatura é um arquivo separado, em Base64.

## 5. Fluxo de verificação

```
Documento + assinatura
          ↓
Recalcula SHA-256 do documento recebido
          ↓
Verificação com chave pública
          ↓
Assinatura válida  ✓  /  inválida  ✕
```

Se um único byte do documento mudar, o SHA-256 muda completamente (efeito avalanche), o hash deixa
de corresponder ao que foi assinado e a verificação falha.

## 6. Instalação

```bash
pip install -r requirements.txt
```

## 7. Execução

```bash
python app.py
```

Abra **http://localhost:5000** no navegador.

## 8. Roteiro da demonstração (≈ 3 min)

A pasta `exemplos/` já traz dois PDFs **idênticos exceto por um único caractere** (nota `7.5` → `9.5`):

1. Aba **ASSINAR**: selecione `exemplos/declaracao_original.pdf` e clique **Assinar documento**.
2. Mostre o **hash SHA-256** e a confirmação da assinatura. Clique em **Baixar assinatura**.
3. Aba **VERIFICAR**: envie `declaracao_original.pdf` + `declaracao_original.pdf.sig` → **✓ Documento autêntico** (verde).
4. Abra os dois PDFs lado a lado: a única diferença é a nota.
5. Envie `declaracao_adulterada.pdf` + **a mesma** assinatura → **✕ Documento adulterado ou assinatura inválida** (vermelho).
6. Compare o hash exibido com o do passo 2: mudou completamente por causa de 1 caractere.

> Dica: faça um ensaio antes para que as chaves já estejam geradas. Elas são reutilizadas entre execuções,
> então uma assinatura gerada no ensaio continua válida no dia da apresentação.
