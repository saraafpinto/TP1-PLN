import re

# 1. Ler o XML original
with open("diccionari.xml", "r", encoding="utf-8") as f:
    xml_bruto = f.read()

# 2. Separar por páginas
paginas = re.findall(r'<page number="(\d+)".*?>(.*?)</page>', xml_bruto, flags=re.S)
xml_estruturado = '<?xml version="1.0" encoding="UTF-8"?>\n<pdf2xml>\n'

print("A processar e ordenar colunas...")

for num, conteudo in paginas:
    # REGEX MELHORADO: Apanha top e left e ignora o resto dos atributos
    # Grupo 1: top, Grupo 2: left, Grupo 3: font, Grupo 4: conteúdo
    tags = re.findall(r'<text[^>]*top="(\d+)"[^>]*left="(\d+)"[^>]*font="(\d+)"[^>]*>(.*?)</text>', conteudo, flags=re.S)
    
    if not tags:
        continue

    # Ordenar: Coluna (left < 450) primeiro, depois altura (top)
    lista_ordenada = sorted(tags, key=lambda x: (1 if int(x[1]) < 450 else 2, int(x[0])))
    
    xml_estruturado += f'<page number="{num}">\n'
    for top, left, font, txt in lista_ordenada:
        # Limpeza de lixo e entidades HTML comuns
        txt_limpo = re.sub(r'<[^>]+>', ' ', txt).strip() # remove tags internas para validar conteúdo
        
        # Filtros de segurança
        if not txt_limpo or txt_limpo in [";", ",", ".", "…"]: 
            continue
        if "QUADERNS 50" in txt_limpo or "DICCIONARI MULTILINGÜE" in txt_limpo:
            continue
            
        # IMPORTANTE: Mantemos o txt original com as tags <b> e <i> para a extração
        xml_estruturado += f'  <text font="{font}" top="{top}" left="{left}">{txt.strip()}</text>\n'
    xml_estruturado += '</page>\n'

xml_estruturado += '</pdf2xml>'

with open("diccionari_limpo.xml", "w", encoding="utf-8") as f:
    f.write(xml_estruturado)