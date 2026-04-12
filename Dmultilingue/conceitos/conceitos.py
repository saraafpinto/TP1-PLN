import re
import json


# pdftohtml -f 30 -l 182 -texto Dados/diccionari-multilinguee-de-la-covid-19.pdf Dmultilingue/conceitos/diccionari.xml

f = open("diccionari_limpo.xml", "r", encoding="utf8")
texto = f.read()


# ==========================================
# 2. MARCAR OS TERMOS NOVOS
# ==========================================
# Transformamos o número na margem + o termo a negrito numa divisória perfeita
texto = re.sub(r'>\s*\d+\s*</text>\s*<text[^>]*>\s*<b>', r'> [NOVO_TERMO] <b>', texto)

# ==========================================
# 3. ACHATAR E LIMPAR LIXO
# ==========================================
# Limpar cabeçalhos e rodapés das páginas
texto = re.sub(r'QUADERNS 50|DICCIONARI MULTILINGÜE DE LA COVID-19', ' ', texto)
texto = re.sub(r'Diccionari\s+[A-Z]\s+\d+', ' ', texto)

# Apagar as tags HTML do PDF, mantendo apenas <b> e <i> 
texto = re.sub(r'</?(?:pdf2xml|page|fontspec|text)[^>]*>', ' ', texto)
texto = re.sub(r'\s+', ' ', texto)

# ==========================================
# 4. EXTRAÇÃO PURA (FÁCIL E ESTRUTURADA)
# ==========================================
dicionario = {}

idiomas = r"oc|eu|gl|es|en|fr|pt \[PT\]|pt \[BR\]|pt|nl|ar"

# FRONTEIRA SEGURA: Agora a tradução só pára se encontrar outra língua, o CAS, Área Temática ou Nota.
# O negrito (<b>) foi removido daqui para não cortar siglas a meio!
fronteiras = r'(?=<i>\s*(?:' + idiomas + r'|CAS)\s*</i>|[A-ZÀ-Ú\s\-]{4,}\.|Nota:|$)'

# Fatiar o texto gigante na nossa divisória
blocos = texto.split('[NOVO_TERMO]')

for bloco in blocos:
    
    # Se o bloco for vazio, salta e passa ao próximo
    bloco = bloco.strip()
    if bloco == "":
        continue

    # --------------------------------------------------
    # 1. TERMO PRINCIPAL (re.search)
    # --------------------------------------------------
    match_termo = re.search(r'^<b>(.*?)</b>', bloco)
    
    if match_termo:
        termo = match_termo.group(1).strip()
    else:
        termo = ""
        
    # Proteção: Se não houver termo válido, salta este bloco
    if termo == "":
        continue

    # --------------------------------------------------
    # 2. CATEGORIA LÉXICA (re.search)
    # --------------------------------------------------
    match_cat = re.search(r'^<b>.*?</b>\s*<i>(.*?)</i>', bloco)
    
    if match_cat:
        categoria = match_cat.group(1).strip()
    else:
        categoria = ""

    # --------------------------------------------------
    # 3. SINÓNIMOS E SIGLAS (re.findall)
    # --------------------------------------------------
    padrao_sinonimos = r'(?:sigla|sin\.|sin\. compl\.|veg\.|;)\s*<b>(.*?)</b>'
    matches_sinonimos = re.findall(padrao_sinonimos, bloco)
    
    lista_sinonimos = []
    for s in matches_sinonimos:
        s_limpo = s.strip()
        if s_limpo != "":
            lista_sinonimos.append(s_limpo)

    # --------------------------------------------------
    # 4. TRADUÇÕES E SUAS CATEGORIAS (re.findall)
    # --------------------------------------------------
    padrao_traducoes = r'<i>\s*(' + idiomas + r')\s*</i>\s*(.*?)' + fronteiras
    matches_traducoes = re.findall(padrao_traducoes, bloco)
    
    traducoes = {}
    for lang, trad in matches_traducoes:
        lang_limpa = lang.strip()
        
        # Limpar lixo HTML que possa ter ficado no texto da tradução
        trad_limpa = re.sub(r'<[^>]+>', '', trad)
        trad_limpa = trad_limpa.strip(" ;")
        trad_limpa = re.sub(r'\s+', ' ', trad_limpa)
        
        if trad_limpa != "":
            traducoes[lang_limpa] = trad_limpa

    # --------------------------------------------------
    # 5. NÚMERO CAS (re.search)
    # --------------------------------------------------
    padrao_cas = r'<i>\s*CAS\s*</i>\s*(.*?)' + fronteiras
    match_cas = re.search(padrao_cas, bloco)
    
    if match_cas:
        cas = match_cas.group(1).strip()
    else:
        cas = ""

    # --------------------------------------------------
    # 6. ÁREA TEMÁTICA E DEFINIÇÃO (re.search)
    # --------------------------------------------------
    padrao_def = r'([A-ZÀ-Ú\s\-]{4,})\.\s*(.*?)(?=Nota:|$)'
    match_def = re.search(padrao_def, bloco)
    
    if match_def:
        area = match_def.group(1).strip()
        definicao_suja = match_def.group(2)
        definicao = re.sub(r'<[^>]+>', '', definicao_suja).strip()
    else:
        area = ""
        definicao = ""

    # --------------------------------------------------
    # 7. NOTAS (re.search)
    # --------------------------------------------------
    padrao_nota = r'Nota:\s*(.*)'
    match_nota = re.search(padrao_nota, bloco)
    
    if match_nota:
        nota_suja = match_nota.group(1)
        nota = re.sub(r'<[^>]+>', '', nota_suja).strip()
    else:
        nota = ""

    # --------------------------------------------------
    # 8. GUARDAR NO DICIONÁRIO
    # --------------------------------------------------
    dicionario[termo] = {
        "categoria_lexica": categoria,
        "sinonimos": lista_sinonimos,
        "traducoes": traducoes,
        "CAS": cas,
        "area_tematica": area,
        "definicao": definicao,
        "nota": nota
    }

def gera_json(filename, dicionario):
    f_out = open(filename, 'w', encoding='utf8')
    json.dump(dicionario, f_out, indent=4, ensure_ascii=False)
    f_out.close()

gera_json("conceitos_dicionario.json", dicionario)