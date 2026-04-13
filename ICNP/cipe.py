import re
import json


f = open("cipe.xml", "r", encoding="utf8")
texto = f.read()


# ==========================================
# 2. SALVAR A INFORMAÇÃO ÚTIL E DESTRUIR O LIXO
# ==========================================
# Substituímos as tags que têm as margens corretas por marcadores textuais.
# Coluna 1 (Código), Coluna 2 (Termo) e Coluna 3 (Descrição)
texto = re.sub(r'<text[^>]*left="(?:11\d|120)"[^>]*>(.*?)</text>', r'[COD] \1 ', texto)
texto = re.sub(r'<text[^>]*left="(?:23\d|24\d)"[^>]*>(.*?)</text>', r'[TERMO] \1 ', texto)
texto = re.sub(r'<text[^>]*left="(?:50\d|51\d|52\d|530)"[^>]*>(.*?)</text>', r'[DESC] \1 ', texto)

# O GOLPE DE MESTRE: Apagamos todas as tags <text> que sobraram!
# Como os cabeçalhos, datas e números de página não tinham a margem certa,
# eles ainda estão dentro de <text> e vão ser apagados agora mesmo.
texto = re.sub(r'<text[^>]*>.*?</text>', ' ', texto, flags=re.S)

# Limpar todo o HTML restante (<b>, <i>, <page>, etc.)
texto = re.sub(r'<[^>]+>', ' ', texto)

# ==========================================
# 3. EXTRAÇÃO COM GRUPOS DE CAPTURA
# ==========================================
# Capturamos o número, o Eixo, o Termo e a Descrição.
padrao = r'\[COD\]\s*(\d+)\s+([A-Z]+)\s*\[TERMO\]\s*(.*?)(?:\[DESC\]\s*(.*?))?(?=\[COD\]|$)'
conceitos = re.findall(padrao, texto, flags=re.S)

# ==========================================
# 4. CONSTRUÇÃO DO DICIONÁRIO E LIMPEZA
# ==========================================
dicionario_cipe = {}

for codigo, eixo, termo_raw, descricao_raw in conceitos:
    
    # Limpamos os marcadores extra que podem ter ficado a meio de frases longas
    termo = termo_raw.replace("[TERMO]", " ")
    termo = re.sub(r'\s+', ' ', termo).strip()
    
    descricao = descricao_raw.replace("[DESC]", " ")
    descricao = re.sub(r'\s+', ' ', descricao).strip()
    
    # Prevenção: só guarda se tiver capturado texto válido
    if termo:
        dicionario_cipe[codigo] = {
            "eixo": eixo.strip(),
            "termo": termo,
            "definicao": descricao
        }


def gera_json(filename, dicionario):
    f_out = open(filename, 'w', encoding='utf8')
    json.dump(dicionario, f_out, indent=4, ensure_ascii=False)
    f_out.close()

gera_json("cipe.json", dicionario_cipe)
