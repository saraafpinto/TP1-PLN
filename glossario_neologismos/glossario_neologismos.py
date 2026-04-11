import re
import json

# Abrir o ficheiro XML
f = open("glossario_neologismos.txt", "r", encoding="utf8")
texto = f.read()
f.close()

texto = re.sub(r'\f',"", texto)
texto = re.sub(r'^(.*\].*[^\]]$)\n(.*\])', r'\1 \2', texto, flags=re.MULTILINE)
texto = re.sub(r'^(.*[mf]\.)$', r'@\1', texto, flags=re.MULTILINE)
texto = re.sub(r'^(.*\]$)', r'\1#', texto, flags=re.MULTILINE)

conceitos = re.split(r'@', texto)
conceitos_dict = {}

for c in conceitos[1:]:
    # 1. Primeiro extraímos a informação da string 'c'
    elems = re.split(r"\n", c, maxsplit=1)
    
    if len(elems) > 1:
        designacao = elems[0].strip() # Limpa espaços em branco
        corpo = re.split(r'#', elems[1])
        
        # Verifica se o corpo tem a estrutura esperada (traducoes # descricao)
        if len(corpo) >= 2:
            traducoes_raw = corpo[0]
            descricao = re.sub(r'\n', '', corpo[1])
            
            traducoes = re.split(r';', traducoes_raw)
            # Garantir que existem pelo menos duas traduções para não dar IndexError
            ing = traducoes[0].strip() if len(traducoes) > 0 else ""
            esp = traducoes[1].strip() if len(traducoes) > 1 else ""

            # 2. SÓ AGORA criamos a entrada no dicionário com a chave correta
            conceitos_dict[designacao] = {
                "traducao": {
                    "inglês": ing,
                    "espanhol": esp
                },
                "descricao": descricao
            }
    else:
        continue

def gera_json(filename, dados):
    f_out = open(filename, 'w', encoding='utf8')
    # Passamos a lista completa para o json.dump
    json.dump(dados, f_out, indent=4, ensure_ascii=False)
    f_out.close()

# Chamada da função com a lista
gera_json("glossario_neologismos.json", conceitos_dict)