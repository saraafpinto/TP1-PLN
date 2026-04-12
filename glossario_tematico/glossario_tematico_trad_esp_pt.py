import re
import json

#ler ficheiro txt

f = open("glossario_tematico_trad_esp_pt.txt", "r", encoding="utf8") #se der problemas por 
texto = f.read()

texto = re.sub(r'\f',"", texto)
texto = re.sub(r'^[A-Z]$',"", texto)
texto = re.sub(r'Glossário Temático\n\d+',"", texto)
texto = re.sub(r'Monitoramento e Avaliação\n\d+',"", texto)

conceitos = re.split(r"\n", texto, flags=re.MULTILINE)

conceitos_dict = {}
for c in conceitos[1:]:
    elems = re.split(r"– ", c, maxsplit=1)
    if len(elems)>1:
        designacao = elems[0]
        descricao = elems[1]
        conceitos_dict[designacao] = descricao
    else:
        #Fix me
        continue

def gera_json(filename, dicionario):
    f_out= open(filename, 'w', encoding='utf8')
    json.dump(dicionario, f_out, indent=4, ensure_ascii=False )
    f_out.close()

gera_json("glossario_tematico_trad_esp_pt.json", conceitos_dict)