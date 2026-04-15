import re
import json
import os

def carregar_abreviaturas(ficheiro_abreviaturas):
    mapa_plano = {}
    if os.path.exists(ficheiro_abreviaturas):
        with open(ficheiro_abreviaturas, "r", encoding="utf8") as f:
            dados = json.load(f)
            for categoria in dados.values():
                for abrev, extenso in categoria.items():
                    # Se o valor for uma lista (caso do PT), pegar no primeiro elemento
                    if isinstance(extenso, list):
                        mapa_plano[abrev] = extenso[0]
                    else:
                        mapa_plano[abrev] = extenso
    return mapa_plano

def guardar_pendente(conceito, estado_atual, chave_atual, texto):
    texto = texto.strip(" ;")
    if not conceito or not estado_atual or not texto: 
        return
    if estado_atual == 'traducao': 
        conceito["traducoes"][chave_atual] += " " + texto
    elif estado_atual == 'nota': 
        conceito["nota"] += " " + texto
    elif estado_atual == 'cas': 
        conceito["CAS"] += " " + texto
    elif estado_atual == 'sinonimo': 
        conceito["sinonimos"][-1] += " " + texto
    elif estado_atual == 'ver_tambem': 
        conceito["ver_tambem"][-1] += " " + texto
    elif estado_atual == 'definicao': 
        conceito["definicao"] += " " + texto

def tratar_campo_multiplo(lista_original, mapa, ordens, remover_sin=False):
    lista_final = []

    # Ordenar as abreviaturas por tamanho (maiores primeiro) para evitar que "n" substitua o "n" de "n m"
    ordens_abrv = sorted(ordens, key=len, reverse=True)

    for s in lista_original:
        # Normalizar espaços e quebras de linhas
        s_limpo = re.sub(r'\n', ' ', s) 
        s_limpo = re.sub(r'\s+', ' ', s_limpo).strip()

        partes = [p.strip() for p in s_limpo.split(';') if p.strip()]
        
        for p in partes:
            if re.search(r'\bsigla\b', p, flags=re.IGNORECASE):
                p = re.sub(r'\bsigla\s*', '', p, flags=re.IGNORECASE).strip()
            
            # Limpeza de marcadores (sin, sin. compl, veg)
            for abrev in ordens_abrv:
                abrev_esc = re.escape(abrev)
                abrev_esc = abrev_esc.replace(r'\ ', r'\s+')
                pattern = rf'\b{abrev_esc}\.?\s*'

                if re.search(pattern, p, flags=re.IGNORECASE):
                    if "sin" in abrev.lower() or "veg" in abrev.lower():
                        p = re.sub(pattern,"", p).strip()
                    else:
                        # Substituir categorias gramaticais
                        if abrev in mapa:
                            extenso = mapa[abrev]
                            p = re.sub(pattern, f"- {extenso}", p).strip()
                    break
            
            p = re.sub(r'\s+', ' ', p).strip()
            if p: lista_final.append(p)
    return lista_final

def processar_dicionario(txt_input, json_output, ficheiro_abreviaturas):
    # Carregar e preparar o mapa de abreviaturas
    mapa_abrev = carregar_abreviaturas(ficheiro_abreviaturas)

    abrev_ordenadas = sorted(mapa_abrev.keys(), key=len, reverse=True)

    f = open(txt_input, "r", encoding="utf8")
    linhas = [l.strip() for l in f.readlines() if l.strip()]
    f.close()

    dicionario = []
    conceito = None
    estado_atual, chave_atual = None, None
    espera_continuacao = False 
    
    # Padrões de Regex
    padrao_novo_termo = r'^(.*?)\s+\b(n m|n f|n m pl|n f pl|n m, f|n m/f|adj|v tr|v tr/intr|v intr|n)\b$'
    padrao_idioma = r'^(oc|eu|gl|es|en|fr|pt \[PT\]|pt \[BR\]|pt|nl|ar)\s+(.*)'
    padrao_marcador = r'^(CAS|Nota:|sigla|veg\.|sin\. compl\.|sin\.)\s+(.*)'
    padrao_area_def = r'^([A-ZÀ-Ú\s\-]{5,})\.\s*(.*)'
    padrao_continuacao = r'[;,]$'

    for linha in linhas:
        # Limpezas iniciais de números de página/ordem
        linha = re.sub(r'^\d+\s+', '', linha)
        linha = re.sub(r';\s*\d+$', ';', linha)
        
        if not linha or linha.isdigit(): continue

        if espera_continuacao:
            guardar_pendente(conceito, estado_atual, chave_atual, linha)
            espera_continuacao = bool(re.search(padrao_continuacao,linha))
            continue

        tem_marcador = False
        m_idioma = re.match(padrao_idioma, linha)
        m_marcador = re.match(padrao_marcador, linha)
        m_area_def = re.match(padrao_area_def, linha)
        m_termo = re.match(padrao_novo_termo, linha)

        if not any([m_idioma, m_marcador, m_area_def, m_termo]) and conceito:
            # Se o último estado foi nota, definição ou sinónimo, continuamos a acumular
            if estado_atual in ['nota', 'definicao', 'sinonimo', 'traducao', 'cas']:
                guardar_pendente(conceito, estado_atual, chave_atual, linha)
                continue

        if m_idioma:
            tem_marcador = True
            if conceito:
                estado_atual = 'traducao'
                chave_atual = m_idioma.group(1).strip()
                conceito["traducoes"][chave_atual] = m_idioma.group(2).strip(" ;")
                
        elif m_marcador:
            tem_marcador = True
            if conceito:
                tipo = m_marcador.group(1).strip()
                resto = m_marcador.group(2).strip(" ;")
                if tipo == "CAS":
                    estado_atual, conceito["CAS"] = 'cas', resto
                elif tipo == "Nota:":
                    estado_atual, conceito["nota"] = 'nota', resto
                elif tipo == "veg.":
                    estado_atual = 'ver_tambem'
                    conceito["ver_tambem"].append(resto)
                elif tipo == "sigla":
                    estado_atual = 'sigla'
                    conceito["siglas"].append(resto)
                else: 
                    estado_atual = 'sinonimo'
                    conceito["sinonimos"].append(resto)
                    
        elif m_area_def:
            tem_marcador = True
            if conceito:
                estado_atual = 'definicao'
                conceito["area_tematica"] = m_area_def.group(1).strip()
                conceito["definicao"] = m_area_def.group(2).strip()

        elif m_termo and ';' not in linha:
            if conceito: dicionario.append(conceito)
            conceito = {
                "termo": m_termo.group(1).strip(),
                "categoria": m_termo.group(2).strip(),
                "traducoes": {}, "sinonimos": [], "ver_tambem": [], "siglas": [], "CAS": "", "area_tematica": "", "definicao": "", "nota": ""
            }
            estado_atual = None
            espera_continuacao = False
            continue 

        if not tem_marcador and not m_termo:
            guardar_pendente(conceito, estado_atual, chave_atual, linha)
            
        espera_continuacao = bool(re.search(padrao_continuacao, linha))

    if conceito: dicionario.append(conceito)

    # Limpeza e formatação
    for item in dicionario:
        # Separar Notas por número
        if item["nota"]:
            # Primeiro junta tudo numa linha para o split não falhar
            nota_completa = item["nota"].replace('\n', ' ')
            nota_completa = re.sub(r'\s+', ' ', nota_completa).strip()
            
            # Faz o split pelos números
            partes_nota = re.split(r'\s*\b\d\.\s*', nota_completa)
            item["nota"] = [n.strip() for n in partes_nota if n.strip()]

        # Sinónimos e Ver_Tambem
        item["sinonimos"] = tratar_campo_multiplo(item["sinonimos"], mapa_abrev, abrev_ordenadas)
        item["ver_tambem"] = tratar_campo_multiplo(item["ver_tambem"], mapa_abrev, abrev_ordenadas)
        item["siglas"] = tratar_campo_multiplo(item["siglas"], mapa_abrev, abrev_ordenadas)

        # Substituir abreviaturas nas traduções
        for lang in item["traducoes"]:
            trad = item["traducoes"][lang].replace('\n', ' ')
            trad = re.sub(r'\s+', ' ', trad)
            
            for abrev in mapa_abrev:
                extenso = mapa_abrev[abrev]
                abrev_esc = re.escape(abrev)
                pattern = rf'\b{abrev_esc}' if abrev.endswith('.') else rf'\b{abrev_esc}\b'
                
                trad = re.sub(pattern, f"- {extenso}", trad)
            
            item["traducoes"][lang] = trad.strip()

        # Substituir na categoria principal
        if item["categoria"] in mapa_abrev:
            item["categoria"] = mapa_abrev[item["categoria"]]

    with open(json_output, 'w', encoding='utf8') as f_out:
        json.dump(dicionario, f_out, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    processar_dicionario('dicionario_bruto.txt', 'dicionario_conceitos.json', '../abreviaturas/abreviaturas_dicionario.json')