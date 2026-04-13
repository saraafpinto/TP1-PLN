import re
import json

#ler ficheiro txt

f = open("medicina.txt", "r", encoding="utf8") #se der problemas por 
texto = f.read()

# 1. Normalizar espaços e tabs
texto = re.sub(r'\n([^#\n]+?)\s+(Vid\.-[^\n]+)', r'\n#\1 \2#', texto)
texto = re.sub(r'(?m)^[ \t]*(es|en|pt|la)\b', r'$\1', texto)
texto = re.sub(r'^\d+\n', '\n', texto, flags=re.MULTILINE)
texto = re.sub(r'\s+Vocabulario\s+', '\n', texto)
texto = re.sub(r'(?<! [mfa])\n([a-z])', r' \1', texto)
texto = re.sub(r'\b(\d+)\b', r'@\1', texto)
conceitos = re.split(r"@", texto) 

conceitos_dict = {}
for c in conceitos[1:]:
    partes = c.strip().split('\n', 1)
    if len(partes) < 2: continue
    
    cabecalho, corpo = partes
    
    # Extrair ID, Nome e Género do cabeçalho
    match_c = re.search(r'^(\d+)\s+(.*?)(?:\s+([mfa]))?$', cabecalho.strip())
    if match_c:
        id_n = match_c.group(1)
        designacao = match_c.group(2).strip()
        gen = match_c.group(3) if match_c.group(3) else ""
        
        conceitos_dict[designacao] = {
            "id": id_n,
            "genero": gen,
            "categoria": "",
            "traducoes": {},
            "sinonimos": [],
            "variantes": [],
            "nota": "",
            "entrada_extra": {}
        }

        match_v = re.findall(r'#(.*?)#', corpo)
        if match_v:
            for bloco in match_v:
                    # Separar o Nome do Vid.-
                    # partes[0] = nome, partes[1] = "Vid.-", partes[2] = referência
                    partes = re.split(r'\s*(Vid\.-)', bloco)
                    
                    if len(partes) >= 3:
                        entrada_nome = partes[0].strip()
                        vid_referencia = (partes[1] + partes[2]).strip()
                        
                        if entrada_nome:
                            conceitos_dict[designacao]["entrada_extra"][entrada_nome] = vid_referencia
                    corpo = corpo.replace(f"#{bloco}#", "")

        corpo = re.sub(r'[ \t]+', ' ', corpo)
        corpo_unido = re.sub(r'\s+', ' ', corpo).strip()

        # 2. TENTAR EXTRAIR A ÁREA (Tudo o que vem antes da primeira sigla ou marcador)
        # Procuramos o início até encontrar 'es ', 'en ', 'pt ', 'la ', 'SIN.-' ou 'Nota.-'
        match_cat = re.search(r'^(.*?)(?=\s*(?:\$|es|en|pt|la|SIN\.-|VAR\.-|Nota\.-))', corpo_unido)
        if match_cat:
            conceitos_dict[designacao]["categoria"] = match_cat.group(1).strip()
        else:
            # Se não encontrar nenhuma sigla, assume que o corpo todo é a área (ou está vazio)
            if not any(x in corpo_unido for x in ['es ', 'en ', 'pt ', 'la ', 'SIN.-']):
                conceitos_dict[designacao]["categoria"] = corpo_unido

        # 4. EXTRAIR SINÓNIMOS (SIN.-)
        m_sin = re.search(r'SIN\.-\s+(.*?)(?=\s*(?:\$|Nota\.-|VAR\.-|Vid\.-|#)|$)', corpo_unido)
        if m_sin:
            # Limpamos possíveis pontos finais no fim da lista de sinónimos antes do split
            sins_raw = m_sin.group(1).strip().rstrip('.')
            sins = sins_raw.split(';')
            conceitos_dict[designacao]["sinonimos"] = [s.strip() for s in sins]

        # 4. EXTRAIR Variantes (VAR)
        m_sin = re.search(r'VAR\.-\s+(.*?)(?=\s*(?:\$|Nota\.-|Vid\.-|#)|$)', corpo_unido)
        if m_sin:
            # Limpamos possíveis pontos finais no fim da lista de sinónimos antes do split
            sins_raw = m_sin.group(1).strip().rstrip('.')
            sins = sins_raw.split(';')
            conceitos_dict[designacao]["variantes"] = [s.strip() for s in sins]

        # 5. EXTRAIR NOTAS (Nota.-)
        m_nota = re.search(r'Nota\.-\s+(.*?)(?=\s*(?:\b(?:es|en|pt|la)\b|SIN\.|-VAR\.-|Vid\.-|#)|$)', corpo_unido)
        if m_nota:
            conceitos_dict[designacao]["nota"] = m_nota.group(1).strip()
            corpo_unido = corpo_unido.replace(m_nota.group(0), "")

        # 3. EXTRAIR TRADUÇÕES
        corpo_unido = re.sub(r'\s+', ' ', corpo).strip()
        for lang in ['es', 'en', 'pt', 'la']:
            # O padrão agora procura: § + sigla + espaço + tudo até ao próximo § ou fim
            padrao = fr'\${lang}\s+(.*?)(?=\s*\$|$)'
            
            match_lang = re.search(padrao, corpo_unido)
            if match_lang:
                # Extraímos o conteúdo e limpamos qualquer marcador residual
                conteudo = match_lang.group(1).strip()
                
                # Segurança extra para o caso do 'la' ainda aparecer no fim
                # (Se a nota ou o SIN não foram marcados com §, paramos neles)
                for stop in ['SIN.-', 'Nota.-', 'Vid.-', '#']:
                    conteudo = conteudo.split(stop)[0].strip()
                    
                conceitos_dict[designacao]["traducoes"][lang] = conteudo


        fim_traducoes = 0
        for m in re.finditer(r'\b(es|en|pt|la|SIN\.-|Nota\.-)\s+', corpo_unido):
            fim_traducoes = m.end()
        
        bloco_final = corpo_unido[fim_traducoes:].strip()

def gera_json(filename, dicionario):
    f_out= open(filename, 'w', encoding='utf8')
    json.dump(dicionario, f_out, indent=4, ensure_ascii=False )
    f_out.close()

gera_json("medicina.json", conceitos_dict)