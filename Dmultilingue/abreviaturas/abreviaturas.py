import re
import json


# pdftohtml -f 29 -l 29 -xml Dados/diccionari-multilinguee-de-la-covid-19.pdf Dados/abreviaturas.xml 

f = open("Dados/abreviaturas.xml", "r", encoding="utf8")
texto = f.read()

# Apanha a posição esquerda (left), a fonte (font) e o texto de todas as tags <text>
tags_brutas = re.findall(r'<text[^>]*left="(\d+)"[^>]*font="([34])"[^>]*>(.*?)</text>', texto)

# Limpar tags <b> de dentro dos textos
elementos = []
for left, font, texto in tags_brutas:
    texto_limpo = re.sub(r'<[^>]+>', '', texto).strip()
    if texto_limpo:
        elementos.append((left, font, texto_limpo))

resultado = {}
categoria_atual = "Sem Categoria"
i = 0

# Dicionario
while i < len(elementos):
    left, font, texto = elementos[i]
    
    # REGRA 1: Título da Categoria (Fonte 3)
    if font == "3":
        categoria_atual = texto
        if categoria_atual not in resultado:
            resultado[categoria_atual] = {}
        i += 1
        continue
        
    # REGRA 2: Abreviação (Fonte 4 e alinhada à esquerda na coluna: 63 ou 442)
    if font == "4" and left in ["63", "442"]:
        abrev = ""
        desc = ""
        
        # O próximo elemento é a descrição? (Verifica se está mais à direita: ex. 122, 144, 493)
        if i + 1 < len(elementos) and elementos[i+1][1] == "4" and elementos[i+1][0] not in ["63", "442"]:
            # O PDF separou em duas tags: [Abrev] -> [Desc]
            abrev = texto
            desc = elementos[i+1][2]
            i += 2 # Saltamos a descrição porque já a guardámos
            
        else:
            # Tentar partir por 2 ou mais espaços (resolve o "v tr/intr", "sin. compl.")
            partes = re.split(r'\s{2,}', texto)
            
            if len(partes) == 2:
                abrev, desc = partes[0], partes[1]
            else:
                # Se falhar, é porque só tem 1 espaço (Ex: "n nom", "adj adjectiu")
                # Então partimos no primeiro espaço que aparecer
                partes = texto.split(" ", 1)
                abrev = partes[0]
                desc = partes[1] if len(partes) > 1 else ""
            i += 1
            
        # GUARDAR O DADO 
        if abrev in resultado[categoria_atual]:
            existente = resultado[categoria_atual][abrev]
            if isinstance(existente, list):
                existente.append(desc)
            else:
                resultado[categoria_atual][abrev] = [existente, desc]
        else:
            resultado[categoria_atual][abrev] = desc

    else:
        # Lixo ou formatações estranhas, avança
        i += 1

def gera_json(filename, dicionario):
    f_out = open(filename, 'w', encoding='utf8')
    json.dump(dicionario, f_out, indent=4, ensure_ascii=False)
    f_out.close()

gera_json("abreviaturas_dicionario.json", resultado)