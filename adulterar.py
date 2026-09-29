"""
Simula um ATACANTE que altera um PDF já assinado.

Uso:   python adulterar.py declaracao_original_assinado.pdf
       python adulterar.py arquivo.pdf "texto antigo" "texto novo"   (mesmo tamanho)

Por padrão troca a nota "7.5" por "9.5": apenas 1 byte do arquivo é modificado.
O resultado é salvo como <arquivo>_adulterado.pdf (o original não é tocado).
"""
import sys
from pathlib import Path

arquivo = Path(sys.argv[1])
antigo = (sys.argv[2] if len(sys.argv) > 2 else "nota final: 7.5").encode("latin-1")
novo = (sys.argv[3] if len(sys.argv) > 3 else "nota final: 9.5").encode("latin-1")

conteudo = arquivo.read_bytes()
if len(antigo) != len(novo):
    sys.exit("Os textos precisam ter o mesmo tamanho (para não quebrar a estrutura do PDF).")
if conteudo.count(antigo) != 1:
    sys.exit(f"Texto {antigo!r} não encontrado exatamente uma vez no arquivo.")

adulterado = conteudo.replace(antigo, novo)
destino = arquivo.with_name(arquivo.stem + "_adulterado.pdf")
destino.write_bytes(adulterado)

diferentes = sum(a != b for a, b in zip(conteudo, adulterado))
print(f"{antigo.decode()!r} -> {novo.decode()!r}  |  {diferentes} byte(s) alterado(s)  |  salvo em {destino.name}")
