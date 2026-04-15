import re
import json


f = open("cipe.xml", "r", encoding="utf8")
texto = f.read()
f.close() 

# Substituir as tags que têm as margens corretas por marcadores textuais
# Coluna 1 (Código), Coluna 2 (Termo) e Coluna 3 (Descrição)
texto = re.sub(r'<text[^>]*left="(?:11\d|120)"[^>]*>(.*?)</text>', r'[COD] \1 ', texto)
texto = re.sub(r'<text[^>]*left="(?:23\d|24\d)"[^>]*>(.*?)</text>', r'[TERMO] \1 ', texto)
texto = re.sub(r'<text[^>]*left="(?:50\d|51\d|52\d|530)"[^>]*>(.*?)</text>', r'[DESC] \1 ', texto)

# Apagar todas as tags <text> que sobraram
texto = re.sub(r'<text[^>]*>.*?</text>', ' ', texto, flags=re.DOTALL)

# Limpar todo o HTML restante (<b>, <i>, <page>, etc.)
texto = re.sub(r'<[^>]+>', ' ', texto)

# Capturar o número, o Eixo, o Termo e a Descrição.
padrao = r'\[COD\]\s*(\d+)\s+([A-Z]+)\s*\[TERMO\]\s*(.*?)(?:\[DESC\]\s*(.*?))?(?=\[COD\]|$)'
conceitos = re.findall(padrao, texto, flags=re.DOTALL)

dicionario_cipe = {}

for codigo, eixo, termo_raw, descricao_raw in conceitos:
    
    # Limpar os marcadores extra 
    termo = termo_raw.replace("[TERMO]", " ")
    termo = re.sub(r'\s+', ' ', termo).strip()
    
    descricao = descricao_raw.replace("[DESC]", " ")
    descricao = re.sub(r'\s+', ' ', descricao).strip()
    
    if termo:
        dicionario_cipe[termo] = {
            "id": codigo,
            "eixo": f'eixo {eixo.strip()}',
            "definicao": descricao
        }


def gera_json(filename, dicionario):
    f_out = open(filename, 'w', encoding='utf8')
    json.dump(dicionario, f_out, indent=4, ensure_ascii=False)
    f_out.close()

gera_json("cipe.json", dicionario_cipe)
