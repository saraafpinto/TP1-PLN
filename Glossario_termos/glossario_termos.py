import re
import json

# ==========================================
# 1. LER O FICHEIRO XML
# ==========================================
f = open("glossario_termos.xml", "r", encoding="utf8")
texto = f.read()


# ==========================================
# 2. ACHATAMENTO E LIMPEZA INICIAL
# ==========================================
# Removemos tags estruturais, mantendo apenas o recheio: <b> e <i>
texto = re.sub(r'</?pdf2xml.*?>', ' ', texto)
texto = re.sub(r'</?page.*?>', ' ', texto)
texto = re.sub(r'<fontspec.*?>', ' ', texto)
texto = re.sub(r'</?text.*?>', ' ', texto)

# Limpeza dos lixos do cabeçalho
texto = re.sub(r'Glossário de Termos.*?Portugal\)', ' ', texto, flags=re.S)
texto = re.sub(r'Fonte:.*?Languages', ' ', texto, flags=re.S)
texto = re.sub(r'Observação:.*?Linguistics\.', ' ', texto, flags=re.S)

# Remover as letras do alfabeto soltas (A, B, C...)
texto = re.sub(r'\b<b>[A-ZÀ-Ú]</b>\b', ' ', texto, flags=re.I)

# ==========================================
# 3. COLAR AS METADES (O Segredo!)
# ==========================================
# Colamos APENAS as tags de itálico (<i>), porque as definições populares
# são frases longas que o PDF partiu em várias linhas.
# NÃO colamos as tags <b> para evitar o erro do "depressão abcesso"!
texto = re.sub(r'</i>\s*<i>', ' ', texto)

# ==========================================
# 4. EXTRAÇÃO COM REGEX "CIRÚRGICO"
# ==========================================
# Usamos [^<]+ (apanha tudo o que NÃO for um '<') 
# Isto garante que o Regex nunca engole outras tags HTML por engano!

# Padrão 1: Itálico (Significado) -> "(pop) ," -> Negrito (Termo)
padrao_1 = r'<i>([^<]+)</i>\s*\(pop\)\s*,\s*<b>([^<]+)</b>'
extraidos_1 = re.findall(padrao_1, texto, flags=re.S)

# Padrão 2: Negrito (Termo) -> "," -> Itálico (Significado) -> "(pop)"
padrao_2 = r'<b>([^<]+)</b>\s*,\s*<i>([^<]+)</i>\s*\(pop\)'
extraidos_2 = re.findall(padrao_2, texto, flags=re.S)

# Colocamos tudo numa única lista garantindo a ordem: (Termo, Significado)
conceitos = [(termo, significado) for significado, termo in extraidos_1]
conceitos += [(termo, significado) for termo, significado in extraidos_2]

# ==========================================
# 5. CONSTRUÇÃO DO DICIONÁRIO
# ==========================================
dicionario_medico = {}

for termo_raw, significado_raw in conceitos:
    
    # Limpar espaços extra (substitui duplos espaços por um simples)
    termo = re.sub(r'\s+', ' ', termo_raw).strip()
    significado = re.sub(r'\s+', ' ', significado_raw).strip()

    if termo and significado:
        # 1. Proteção contra inversões (ex: acomodação/adaptação)
        if significado in dicionario_medico and termo in dicionario_medico[significado]["significado"]:
            continue
            
        # 2. Juntar significados ao mesmo termo
        elif termo in dicionario_medico:
            if significado not in dicionario_medico[termo]["significado"]:
                dicionario_medico[termo]["significado"] += f" / {significado}"
                
        # 3. Termo novo
        else:
            dicionario_medico[termo] = {"significado": significado}

# ==========================================
# 3. EXPORTAR PARA JSON
# ==========================================
def gera_json(filename, dicionario):
    f_out = open(filename, 'w', encoding='utf8')
    json.dump(dicionario, f_out, indent=4, ensure_ascii=False)
    f_out.close()

gera_json("glossario_termos.json", dicionario_medico)
