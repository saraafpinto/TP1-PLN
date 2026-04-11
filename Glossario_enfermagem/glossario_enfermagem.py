import re
import json

# 1. Carregar o XML como texto
f = open("../Dados/glossario_enfermagem.xml", "r", encoding="utf8")
texto = f.read()
f.close()

# 2. Limpeza de tags irrelevantes, mas mantendo a estrutura <b>
# Removemos as tags <text...>, <page...>, <fontspec...>, etc.
texto = re.sub(r'</?text.*?>', ' ', texto)
texto = re.sub(r'</?page.*?>', ' ', texto)

texto = re.sub(r'</i></text>\s*<text.*?><i>', '', texto)
texto = re.sub(r'&amp;', r'', texto)
texto = re.sub(r'lter', r'filter', texto)


padrao = r'(?<!<i>)<b>(.*?)</b>\s*(.*?)(?=(?<!<i>)<b>|$)'
conceitos = re.findall(padrao, texto, flags=re.S)

res = {}
for termo, bloco_texto in conceitos:
    # Limpeza inicial do bloco de texto (remover tags <text>, etc.)
    # Mas mantemos os espaços originais por agora para não colar palavras
    bloco_limpo = re.sub(r'</?text.*?>', ' ', bloco_texto)
    bloco_limpo = re.sub(r'<.*?>', '', bloco_limpo) # Remove <i>, etc.
    
    # 3. SEPARAÇÃO (Definição vs Fonte)
    if "FONTE:" in bloco_limpo:
        partes = bloco_limpo.split("FONTE:")
        definicao_raw = partes[0]
        fonte_raw = partes[1]
    else:
        definicao_raw = bloco_limpo
        fonte_raw = ""

    # --- REGRAS PARA A DEFINIÇÃO ---
    # Substituímos múltiplas quebras de linha/espaços por UM espaço
    definicao = re.sub(r'\s+', ' ', definicao_raw).strip()
    # Consertar palavras cortadas conhecidas
    definicao = definicao.replace("nanceiros", "financeiros")
    definicao = definicao.replace("exploração a;", "exploração física;")

    # --- REGRAS PARA A FONTE (LINK) ---
    # Aqui podemos ser agressivos com os espaços porque links não os devem ter
    fonte = re.sub(r'\s+', ' ', fonte_raw).strip()
    if "http" in fonte:
        # Colar o link (ex: "idos o" -> "idoso")
        fonte = re.sub(r'(?<=[a-z0-9])\s+(?=[a-z0-9#])', '', fonte, flags=re.I)
        # Consertar parâmetros do DeCS
        fonte = fonte.replace("termallq=", "termall&q=")
        fonte = fonte.replace("?id=", "?id=")
        fonte = fonte.replace("lter=", "filter=").replace("lt er=", "filter=")

    # 4. GUARDA NO DICIONÁRIO
    termo_final = termo.strip()
    if termo_final and "Glossário" not in termo_final and not termo_final.isdigit():
        res[termo_final] = {
            "definicao": definicao,
            "fonte": fonte
        }

# 4. Gravar o JSON
f_out = open("glossario_enfermagem.json", "w", encoding="utf-8")
json.dump(res, f_out, indent=4, ensure_ascii=False)
f_out.close()
