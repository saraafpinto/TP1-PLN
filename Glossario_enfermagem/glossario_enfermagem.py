import re
import json

# Abrir o ficheiro XML
f = open("glossario_enfermagem.xml", "r", encoding="utf8")
texto = f.read()
f.close()

# Apaga os números de página 
texto = re.sub(r'<b>\d+</b>', ' ', texto)  

texto = re.sub(r'<b>GLOSSÁRIO DA LINGUAGEM ESPECIAL DE ENFERMAGEM</b>', ' ', texto)
texto = re.sub(r'<b>PARA A PRÁTICA JUNTO A POVOS INDÍGENAS NO CONTEXTO AMAZÔNICO</b>', ' ', texto)

# Limpeza de tags irrelevantes
texto = re.sub(r'</?text.*?>', ' ', texto)
texto = re.sub(r'</?page.*?>', ' ', texto)

texto = re.sub(r'</i></text>\s*<text.*?><i>', '', texto)
texto = re.sub(r'&amp;', r'', texto)

texto = re.sub(r'</b>\s*<b>', ' ', texto)

padrao = r'(?<!<i>)<b>(.*?)</b>\s*(.*?)(?=(?<!<i>)<b>|$)'
conceitos = re.findall(padrao, texto, flags=re.S)

res = {}
for termo, bloco_texto in conceitos:
    # Limpeza inicial do bloco de texto
    bloco_limpo = re.sub(r'</?text.*?>', ' ', bloco_texto)
    # Remove <i>
    bloco_limpo = re.sub(r'<.*?>', '', bloco_limpo) 
    
    # separação da definição da fonte
    if "FONTE:" in bloco_limpo:
        partes = bloco_limpo.split("FONTE:")
        definicao_raw = partes[0]
        fonte_raw = partes[1]
    else:
        definicao_raw = bloco_limpo
        fonte_raw = ""

    # Substituir múltiplas quebras de linha/espaços por UM espaço
    definicao = re.sub(r'\s+', ' ', definicao_raw).strip()
    # Consertar palavras cortadas conhecidas
    definicao = definicao.replace("nanceiros", "financeiros")
    definicao = definicao.replace("exploração a;", "exploração física;")


    # Retirar os espaços no meio dos links 
    fonte = re.sub(r'\s+', ' ', fonte_raw).strip()
    if "http" in fonte:
        # Colar o link 
        fonte = re.sub(r'(?<=[a-z0-9])\s+(?=[a-z0-9#])', '', fonte, flags=re.I)
        # Consertar parâmetros do DeCS
        fonte = fonte.replace("termallq=", "termall&q=")
        fonte = fonte.replace("?id=", "?id=")
        fonte = fonte.replace("lter=", "filter=").replace("lt er=", "filter=")

    # Guardar no dicionário 
    termo_final = termo.strip()
    if termo_final and "Glossário" not in termo_final and not termo_final.isdigit():
        res[termo_final] = {
            "definicao": definicao,
            "fonte": fonte
        }

def gera_json(filename, dicionario):
    f_out= open(filename, 'w', encoding='utf8')
    json.dump(dicionario, f_out, indent=4, ensure_ascii=False )
    f_out.close()

gera_json("glossario_enfermagem.json", res)