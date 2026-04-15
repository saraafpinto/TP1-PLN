import re
import json

f = open("medicina_latino.txt", "r", encoding="utf8") 
texto = f.read()
f.close() 

texto = re.sub(r'\s+Índice de denominacións latinas\s+\d+\n', '\n', texto)
texto = re.sub(r'([a-z])\n([a-z])', r'\1 \2', texto)

conceitos = re.split(r"\n", texto, flags=re.MULTILINE)

conceitos_dict = {}
for c in conceitos[1:]:
    elems = re.split(r", ", c, maxsplit=1)
    if len(elems)>1:
        designacao = elems[0]
        descricao = elems[1]
        conceitos_dict[designacao] = descricao
    else:
        continue

def gera_json(filename, dicionario):
    f_out= open(filename, 'w', encoding='utf8')
    json.dump(dicionario, f_out, indent=4, ensure_ascii=False )
    f_out.close()

gera_json("medicina_latino.json", conceitos_dict)