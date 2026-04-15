import re
import json

# Abrir o ficheiro TXT
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
    elems = re.split(r"\n", c, maxsplit=1)
    
    if len(elems) > 1:
        #Tratamento da designacao e do género
        linha_termo = elems[0].strip()
        match_genero = re.search(r'(.*)\s+(s\.[mf]\.)$', linha_termo)
        
        genero = ""
        designacao = linha_termo
        
        if match_genero:
            designacao = match_genero.group(1).strip()
            sigla_gen = match_genero.group(2).strip()
            if sigla_gen == "s.f.":
                genero = "feminino"
            elif sigla_gen == "s.m.":
                genero = "masculino"

        corpo_split = re.split(r'#', elems[1])
        
        if len(corpo_split) >= 2:
            traducoes_raw = corpo_split[0]
            resto_corpo = corpo_split[1].strip()
            
            # Limpeza das traduções (Retirar [ing] e [esp])
            traducoes_lista = re.split(r';', traducoes_raw)
            ing_raw = traducoes_lista[0].strip() if len(traducoes_lista) > 0 else ""
            esp_raw = traducoes_lista[1].strip() if len(traducoes_lista) > 1 else ""
            
            ing = re.sub(r'\s*\[ing\]', '', ing_raw, flags=re.IGNORECASE).strip()
            esp = re.sub(r'\s*\[esp\]', '', esp_raw, flags=re.IGNORECASE).strip()

            # Extração de sigla, descrição e Inf. Encicl
            pesquisa = ""
            match_pesquisa = re.search(r'[“"](.*?)[”"]', resto_corpo, flags=re.DOTALL)
            if match_pesquisa:
                pesquisa = match_pesquisa.group(1).replace('\n', ' ').strip()
                # Remover a citação do corpo de texto para a definicao ficar limpa
                resto_corpo = re.sub(match_pesquisa.group(0), '', resto_corpo).strip()

            sigla_termo = ""
            match_sigla = re.search(r'Sigla:\s*(\w+)', resto_corpo)
            if match_sigla:
                sigla_termo = match_sigla.group(1)
                # Remover a linha da sigla para não sujar a definicao
                resto_corpo = re.sub(r'Sigla:\s*\w+\n?', '', resto_corpo).strip()

            # Separar Descrição de Inf. Encicl.
            inf_encicl = ""
            definicao = resto_corpo
            if "Inf. encicl.:" in resto_corpo:
                partes_def = re.split(r'Inf\. encicl\.:', resto_corpo)
                definicao = partes_def[0].strip()
                inf_encicl = partes_def[1].strip()

            # Limpar quebras de linha extras
            definicao = re.sub(r'\n', ' ', definicao).strip()
            inf_encicl = re.sub(r'\n', ' ', inf_encicl).strip()

            # Contrução do dicionário 
            conceitos_dict[designacao] = {
                "genero": genero,
                "sigla": sigla_termo,
                "traducao": {
                    "inglês": ing,
                    "espanhol": esp
                },
                "definição": definicao,
                "inf_encicl": inf_encicl,
                "pesquisa": pesquisa
            }
    else:
        continue

def gera_json(filename, dados):
    f_out = open(filename, 'w', encoding='utf8')
    json.dump(dados, f_out, indent=4, ensure_ascii=False)
    f_out.close()

gera_json("glossario_neologismos.json", conceitos_dict)