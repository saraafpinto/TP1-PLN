import re
import json
import os

def carregar_abreviaturas(ficheiro_abreviaturas):
    """Carrega e aplana o mapa de abreviaturas aninhado."""
    mapa_plano = {}
    if os.path.exists(ficheiro_abreviaturas):
        with open(ficheiro_abreviaturas, "r", encoding="utf8") as f:
            dados = json.load(f)
            for categoria in dados.values():
                for abrev, extenso in categoria.items():
                    # Se o valor for uma lista (caso do PT), pegamos no primeiro elemento
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
    for s in lista_original:
        # Aplanar quebras de linha e normalizar espaços
        s_limpo = s.replace('\n', ' ')
        s_limpo = re.sub(r'\s+', ' ', s_limpo).strip()

        # Separar por ';' ANTES de remover abreviaturas para não perder o corte
        partes = s_limpo.split(';')
        
        for p in partes:
            p = p.strip()
            if not p: continue
            
            # Limpeza de marcadores (sin, sin. compl, veg)
            for abrev in ordens:
                abrev_esc = re.escape(abrev)
                pattern = re.compile(rf'\b{abrev_esc}' if abrev.endswith('.') else rf'\b{abrev_esc}\b')
                
                if "sin" in abrev or "veg" in abrev:
                    p = pattern.sub("", p).strip()
                else:
                    # Substituir categorias gramaticais
                    if abrev in mapa:
                        p = pattern.sub(f"- {mapa[abrev]}", p).strip()
            
            p = re.sub(r'\s+', ' ', p).strip()
            if p: lista_final.append(p)
    return lista_final

def processar_dicionario(txt_input, json_output, ficheiro_abreviaturas):
    # 1. Carregar e preparar o mapa de abreviaturas
    mapa_abrev = carregar_abreviaturas(ficheiro_abreviaturas)
    
    # Ordenar as abreviaturas por tamanho (maiores primeiro) 
    # para evitar que "n" substitua o "n" de "n m"
    abrev_ordenadas = sorted(mapa_abrev.keys(), key=len, reverse=True)

    f = open(txt_input, "r", encoding="utf8")
    linhas = [l.strip() for l in f.readlines() if l.strip()]
    f.close()

    dicionario = []
    conceito = None
    estado_atual, chave_atual = None, None
    id_gerado = 1
    espera_continuacao = False 
    
    regex_novo_termo = re.compile(r'^(.*?)\s+\b(n m|n f|n m pl|n f pl|n m, f|n m/f|adj|v tr|v tr/intr|v intr|n)\b$')
    regex_idioma = re.compile(r'^(oc|eu|gl|es|en|fr|pt \[PT\]|pt \[BR\]|pt|nl|ar)\s+(.*)')
    regex_marcador = re.compile(r'^(CAS|Nota:|sigla|veg\.|sin\.|sin\. compl\.)\s+(.*)')
    regex_area_def = re.compile(r'^([A-ZÀ-Ú\s\-]{5,})\.\s*(.*)')
    regex_continuacao = re.compile(r'[;,]$')

    for linha in linhas:
        linha = re.sub(r'^\d+\s+', '', linha)
        linha = re.sub(r';\s*\d+$', ';', linha)
        
        if not linha or linha.isdigit(): continue

        if espera_continuacao:
            guardar_pendente(conceito, estado_atual, chave_atual, linha)
            espera_continuacao = bool(regex_continuacao.search(linha))
            continue

        tem_marcador = False
        m_idioma = regex_idioma.match(linha)
        m_marcador = regex_marcador.match(linha)
        m_area_def = regex_area_def.match(linha)
        m_termo = regex_novo_termo.match(linha)

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
                    # Guardamos sem o prefixo 'veg.', o pós-processamento trata da limpeza
                    conceito["ver_tambem"].append(resto)
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
                "id": id_gerado,
                "termo": m_termo.group(1).strip(),
                "categoria": m_termo.group(2).strip(),
                "traducoes": {}, "sinonimos": [], "ver_tambem": [], "CAS": "", "area_tematica": "", "definicao": "", "nota": ""
            }
            id_gerado += 1
            estado_atual = None
            espera_continuacao = False
            continue 

        if not tem_marcador and not m_termo:
            guardar_pendente(conceito, estado_atual, chave_atual, linha)
            
        espera_continuacao = bool(regex_continuacao.search(linha))

    if conceito: dicionario.append(conceito)

    # ==========================================
    # PÓS-PROCESSAMENTO: LIMPEZA E FORMATAÇÃO
    # ==========================================
    for item in dicionario:
        # 1. Separar Notas por número
        if item["nota"]:
            # Primeiro junta tudo numa linha só para o split não falhar
            nota_completa = item["nota"].replace('\n', ' ')
            nota_completa = re.sub(r'\s+', ' ', nota_completa).strip()
            
            # Agora sim, faz o split pelos números
            partes_nota = re.split(r'\s*\b\d\.\s*', nota_completa)
            item["nota"] = [n.strip() for n in partes_nota if n.strip()]

        # 2. Sinónimos e Ver_Tambem (Aqui chamamos a função que perguntaste!)
        item["sinonimos"] = tratar_campo_multiplo(item["sinonimos"], mapa_abrev, abrev_ordenadas)
        item["ver_tambem"] = tratar_campo_multiplo(item["ver_tambem"], mapa_abrev, abrev_ordenadas)

        # 4. Substituir abreviaturas nas TRADUÇÕES
        for lang in item["traducoes"]:
            trad = item["traducoes"][lang].replace('\n', ' ')
            trad = re.sub(r'\s+', ' ', trad)
            
            for abrev in abrev_ordenadas:
                extenso = mapa_abrev[abrev]
                abrev_esc = re.escape(abrev)
                pattern = re.compile(rf'\b{abrev_esc}' if abrev.endswith('.') else rf'\b{abrev_esc}\b')
                
                trad = pattern.sub(f"- {extenso}", trad)
            
            item["traducoes"][lang] = trad.strip()

        # 5. Substituir na CATEGORIA principal
        if item["categoria"] in mapa_abrev:
            # Aqui podes decidir: ou deixas só o extenso, ou limpas. 
            # Geralmente na categoria quer-se o valor:
            item["categoria"] = mapa_abrev[item["categoria"]]

    with open(json_output, 'w', encoding='utf8') as f_out:
        json.dump(dicionario, f_out, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    processar_dicionario('dicionario_bruto.txt', 'dicionario_conceitos.json', '../abreviaturas/abreviaturas_dicionario.json')