import re
import json

# Abrir o ficheiro XML
f = open("glossario_tematico_conceitos.txt", "r", encoding="utf8")
texto = f.read()
f.close()

texto = re.sub(r'\f',"", texto)
texto = re.sub(r'^[A-Z]$',"", texto)
texto = re.sub(r'Glossário Temático\n\d+\n\w{3}',"", texto)
texto = re.sub(r'Monitoramento e Avaliação\n\d+\n\w{3}',"", texto)
texto = re.sub(r'⇒', "Lê-se como: ", texto)

# Cabeçalho (Termo | Género $)
texto = re.sub(r'^(.*), (fem\.|masc\.)', r'@\1 | \2 $', texto, flags=re.MULTILINE)

# Marcar Sinónimos (Sin. até ao primeiro ponto final)
texto = re.sub(r'(\$\s*)Sin\.\s+(.*?)\.\s+', r'\1#SIN:\2#DEF:', texto)
texto = re.sub(r'\$\s+(?!#SIN:|#DEF:)', r'$ #DEF:', texto)

# Marcar Notas (com ou sem i)
texto = re.sub(r'Nota(s?)?:\s*(?:i\))?', r'#NOTA:', texto)
texto = re.sub(r'\s+[iv]{2,}\)', r'#NOTA:', texto)

# Marcar Remissivas (Ver ...)
texto = re.sub(r'\bVer\s+(.*?)(?=\s*Em espanhol:|Em inglês:|#|\n\n|$)', r'#VER:\1', texto, flags=re.IGNORECASE | re.DOTALL)

# Marcar Traduções
texto = re.sub(r'Em espanhol:', r'#ES:', texto)
texto = re.sub(r'Em inglês:', r'#EN:', texto)

conceitos_dict = {}

# 2. Separar por conceitos (cada um começa com @)
blocos = re.split(r'\n@', texto)

for bloco in blocos:
    if not bloco.strip(): continue
    partes = re.split(r'\$', bloco, maxsplit=1)
    if len(partes) < 2: continue
    
    cabecalho = partes[0].strip().replace('@', '')
    corpo = partes[1].strip()
    termo_principal = cabecalho.split('|')[0].strip()
    
    # Criar objeto base
    res = {
        "genero": cabecalho.split('|')[1].strip() if '|' in cabecalho else "",
        "sinonimo": "",
        "definicao": "",
        "remissa": {},
        "notas": [],
        "traducoes": {}
    }

    # 3. SPLIT POR # E ATRIBUIÇÃO DIRETA
    campos = re.split(r'#', corpo)
    
    for c in campos:
        c = re.sub(r'\n', "", c).strip()
        if not c: continue
        
        if c.startswith("SIN:"):
            res["sinonimo"] = c.replace("SIN:", "").strip()
        elif c.startswith("DEF:"):
            # Aqui guardamos a definição, mas limpamos se o "Ver" ficou lá preso por erro
            def_limpa = c.replace("DEF:", "").strip()
            res["definicao"] = re.split(r'\bVer\b', def_limpa, flags=re.IGNORECASE)[0].strip()
        elif c.startswith("VER:"):
            conteudo_ver = c.replace("VER:", "").strip().replace('\n', ' ').rstrip('.')
            
            # Lógica especial para "Ver sin."
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
            res["notas"].append(c.replace("NOTA:", "").strip())
        elif c.startswith("ES:"):
            res["traducoes"]["espanhol"] = c.replace("ES:", "").strip()
        elif c.startswith("EN:"):
            res["traducoes"]["ingles"] = c.replace("EN:", "").strip()

    conceitos_dict[termo_principal] = res

def gera_json(filename, dados):
    f_out = open(filename, 'w', encoding='utf8')
    # Passamos a lista completa para o json.dump
    json.dump(dados, f_out, indent=4, ensure_ascii=False)
    f_out.close()

# Chamada da função com a lista
gera_json("glossario_tematico_conceitos.json", conceitos_dict)