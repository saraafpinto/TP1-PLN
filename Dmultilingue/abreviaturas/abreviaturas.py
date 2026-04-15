import re
import json


# pdftohtml -f 29 -l 29 -xml Dados/diccionari-multilinguee-de-la-covid-19.pdf Dados/abreviaturas.xml 

f = open("abreviaturas.xml", "r", encoding="utf8")
texto = f.read()
f.close() 


# Transformar as coordenadas XML em etiquetas textuais
# [CAT] -> Títulos de Categoria (font="3")
texto = re.sub(r'<text[^>]*font="3"[^>]*>(.*?)</text>', r'[CAT] \1', texto)

# [L] -> Abreviações que começam na margem esquerda exata (63 ou 442)
texto = re.sub(r'<text[^>]*left="(?:63|442)"[^>]*font="4"[^>]*>(.*?)</text>', r'[L] \1', texto)

# [R] -> Descrições que estão mais à direita (qualquer 'left' diferente de 63 e 442)
texto = re.sub(r'<text[^>]*left="(?!63|442)\d+"[^>]*font="4"[^>]*>(.*?)</text>', r'[R] \1', texto)

# Limpar restantes tags do HTML
texto = re.sub(r'<[^>]+>', '', texto)

# Limpar cabeçalho
texto = re.sub(r'QUADERNS.*?COVID-19', ' ', texto)
texto = re.sub(r'Abreviacions', ' ', texto)


resultado = {}

# NÍVEL 1: bloco inteiro de cada categoria
# [CAT] -> (Nome) -> (Conteúdo até ao próximo [CAT])
padrao_categorias = r'\[CAT\]\s*([^\[]+)(.*?)(?=\[CAT\]|$)'
categorias = re.findall(padrao_categorias, texto, flags=re.S)

for nome_cat, conteudo_cat in categorias:
    nome_cat = nome_cat.strip()
    resultado[nome_cat] = {}

    # NÍVEL 2:cada item dentro dessa categoria
    # Começa no [L] e vai até ao próximo [L] ou até ao fim do bloco
    padrao_itens = r'\[L\]\s*(.*?)\s*(?=\[L\]|$)'
    itens = re.findall(padrao_itens, conteudo_cat, flags=re.S)

    for item in itens:
        item = item.strip()
        if not item: continue

        # --- Separação (Abreviação ou Descrição) ---
        if '[R]' in item:
            partes = item.split('[R]')
            abrev = partes[0].strip()
            desc = partes[1].strip() if len(partes) > 1 else ""

        elif re.search(r'\s{2,}', item):
            # na mesma caixa, mas separada por múltiplos espaços 
            partes = re.split(r'\s{2,}', item, maxsplit=1)
            abrev = partes[0].strip()
            desc = partes[1].strip()

        else:
            # na mesma caixa apenas com um espaço 
            partes = item.split(' ', 1)
            abrev = partes[0].strip()
            desc = partes[1].strip() if len(partes) > 1 else ""

        # --- Guardar ---
        if abrev in resultado[nome_cat]:
            existente = resultado[nome_cat][abrev]
            if isinstance(existente, list):
                existente.append(desc)
            else:
                resultado[nome_cat][abrev] = [existente, desc]
        else:
            resultado[nome_cat][abrev] = desc

def gera_json(filename, dicionario):
    f_out = open(filename, 'w', encoding='utf8')
    json.dump(dicionario, f_out, indent=4, ensure_ascii=False)
    f_out.close()

gera_json("abreviaturas_dicionario.json", resultado)