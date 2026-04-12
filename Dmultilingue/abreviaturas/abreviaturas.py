import re
import json


# pdftohtml -f 29 -l 29 -xml Dados/diccionari-multilinguee-de-la-covid-19.pdf Dados/abreviaturas.xml 

f = open("abreviaturas.xml", "r", encoding="utf8")
texto = f.read()

# ==========================================
# 2. MARCAÇÃO ESTRUTURAL (O Segredo do Regex)
# ==========================================
# Transformamos as coordenadas XML em "Etiquetas textuais" antes de apagar as tags

# [CAT] -> Títulos de Categoria (font="3")
texto = re.sub(r'<text[^>]*font="3"[^>]*>(.*?)</text>', r'[CAT] \1', texto)

# [L] -> Abreviações que começam na margem esquerda exata (63 ou 442)
texto = re.sub(r'<text[^>]*left="(?:63|442)"[^>]*font="4"[^>]*>(.*?)</text>', r'[L] \1', texto)

# [R] -> Descrições que estão mais à direita (qualquer 'left' diferente de 63 e 442)
texto = re.sub(r'<text[^>]*left="(?!63|442)\d+"[^>]*font="4"[^>]*>(.*?)</text>', r'[R] \1', texto)

# Limpamos TODAS as outras tags HTML que sobraram (incluindo as de lixo como <fontspec>)
texto = re.sub(r'<[^>]+>', '', texto)

# Limpar lixos conhecidos do cabeçalho
texto = re.sub(r'QUADERNS.*?COVID-19', ' ', texto)
texto = re.sub(r'Abreviacions', ' ', texto)

# ==========================================
# 3. EXTRAÇÃO EM DOIS NÍVEIS (Regex de Blocos)
# ==========================================
resultado = {}

# NÍVEL 1: Apanhar o bloco inteiro de cada Categoria
# O Regex apanha: [CAT] -> (Nome) -> (Conteúdo até ao próximo [CAT])
padrao_categorias = r'\[CAT\]\s*([^\[]+)(.*?)(?=\[CAT\]|$)'
categorias = re.findall(padrao_categorias, texto, flags=re.S)

for nome_cat, conteudo_cat in categorias:
    nome_cat = nome_cat.strip()
    resultado[nome_cat] = {}

    # NÍVEL 2: Apanhar cada item dentro dessa categoria
    # Começa no [L] e vai até ao próximo [L] ou até ao fim do bloco
    padrao_itens = r'\[L\]\s*(.*?)\s*(?=\[L\]|$)'
    itens = re.findall(padrao_itens, conteudo_cat, flags=re.S)

    for item in itens:
        item = item.strip()
        if not item: continue

        # --- Lógica de Separação (Abreviação vs Descrição) ---
        if '[R]' in item:
            # O PDF separou em duas caixas textuais no XML
            partes = item.split('[R]')
            abrev = partes[0].strip()
            desc = partes[1].strip() if len(partes) > 1 else ""

        elif re.search(r'\s{2,}', item):
            # Estava na mesma caixa, mas separada por múltiplos espaços (ex: sin. compl.)
            partes = re.split(r'\s{2,}', item, maxsplit=1)
            abrev = partes[0].strip()
            desc = partes[1].strip()

        else:
            # Estava na mesma caixa apenas com um espaço (ex: "n nom")
            partes = item.split(' ', 1)
            abrev = partes[0].strip()
            desc = partes[1].strip() if len(partes) > 1 else ""

        # --- GUARDAR O DADO ---
        if abrev in resultado[nome_cat]:
            existente = resultado[nome_cat][abrev]
            if isinstance(existente, list):
                existente.append(desc)
            else:
                resultado[nome_cat][abrev] = [existente, desc]
        else:
            resultado[nome_cat][abrev] = desc

def gera_json(filename, dicionario):
    f_out = open(filename, 'w', encoding='utf8')
    json.dump(dicionario, f_out, indent=4, ensure_ascii=False)
    f_out.close()

gera_json("abreviaturas_dicionario.json", resultado)