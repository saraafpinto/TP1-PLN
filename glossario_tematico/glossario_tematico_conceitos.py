import re
import json

# Abrir o ficheiro TXT
f = open("glossario_tematico_conceitos.txt", "r", encoding="utf8")
texto = f.read()
f.close()

texto = re.sub(r'\f',"", texto)
texto = re.sub(r'^[A-Z]$',"", texto)
texto = re.sub(r'Glossário Temático\n\d+\n\w{3}',"", texto)
texto = re.sub(r'Monitoramento e Avaliação\n\d+\n\w{3}',"", texto)
texto = re.sub(r'⇒', "Lê-se como: ", texto)

# Cabeçalho (@Termo | Género $)
texto = re.sub(r'^(.*), (fem\.|masc\.)', r'@\1 | \2 $', texto, flags=re.MULTILINE)

# Marcar Sinónimos (Sin. até ao primeiro ponto final)
texto = re.sub(r'(\$\s*)Sin\.\s+(.*?)\.\s+', r'\1#SIN:\2#DEF:', texto)
texto = re.sub(r'\$\s+(?!#SIN:|#DEF:)', r'$ #DEF:', texto)

# Marcar Notas (com ou sem i))
texto = re.sub(r'Nota(s?)?:\s*(?:i\))?', r'#NOTA:', texto)
texto = re.sub(r'\s+[iv]{2,}\)', r'#NOTA:', texto)

# Marcar Remissivas (Ver ...)
texto = re.sub(r'\bVer\s+(.*?)(?=\s*Em espanhol:|Em inglês:|#|\n\n|$)', r'#VER:\1', texto, flags=re.IGNORECASE | re.DOTALL)

# Marcar Traduções
texto = re.sub(r'Em espanhol:', r'#ES:', texto)
texto = re.sub(r'Em inglês:', r'#EN:', texto)

conceitos_dict = {}

# Separar por conceitos (cada um começa com @)
blocos = re.split(r'\n@', texto)

for bloco in blocos:
    if not bloco.strip(): continue
    partes = re.split(r'\$', bloco, maxsplit=1)
    if len(partes) < 2: continue
    
    cabecalho = partes[0].strip().replace('@', '')
    corpo = partes[1].strip()
    termo_principal = cabecalho.split('|')[0].strip()
    
    # Criar dicionario base
    res = {
        "genero": cabecalho.split('|')[1].strip() if '|' in cabecalho else "",
        "sinonimo": "",
        "definicao": "",
        "remissa": {},
        "notas": [],
        "traducoes": {}
    }

    # split pelo # e atribuição direta dos parâmetros
    campos = re.split(r'#', corpo)
    
    for c in campos:
        c = re.sub(r'\n', "", c).strip()
        if not c: continue
        
        if c.startswith("SIN:"):
            res["sinonimo"] = re.sub(r"SIN:", "", c).strip()

        elif c.startswith("DEF:"):
            def_limpa = re.sub(r"DEF:", "",c).strip()
            # Verificar se o "Ver" ficou na definição
            res["definicao"] = re.split(r'\bVer\b', def_limpa, flags=re.IGNORECASE)[0].strip()

        elif c.startswith("VER:"):
            conteudo_ver = re.sub(r"VER:", "", c).strip().replace()
            conteudo_ver = re.sub(r'\n', ' ', c).rstrip('.')

            # Lógica para "Ver sin."
            if "sin." in conteudo_ver.lower():
                limpo = re.sub(r'sin\.\s*', '', conteudo_ver, flags=re.IGNORECASE).strip()
                partes_v = [p.strip() for p in limpo.split(';')]
                if len(partes_v) > 1:
                    res["remissa"] = {partes_v[0]: "; ".join(partes_v[1:])}
                else:
                    res["remissa"] = {"sin": partes_v[0]}
            else:
                res["remissa"] = [p.strip() for p in conteudo_ver.split(';')]
        
        elif c.startswith("NOTA:"):
            res["notas"].append(re.sub(r"NOTA:", "",c).strip())
        elif c.startswith("ES:"):
            res["traducoes"]["espanhol"] = re.sub(r"ES:", "",c).strip()
        elif c.startswith("EN:"):
            res["traducoes"]["ingles"] = re.sub(r"EN:", "",c).strip()

    conceitos_dict[termo_principal] = res

def gera_json(filename, dados):
    f_out = open(filename, 'w', encoding='utf8')
    json.dump(dados, f_out, indent=4, ensure_ascii=False)
    f_out.close()

gera_json("glossario_tematico_conceitos.json", conceitos_dict)