import re
import json

# ==========================================
# 1. LER O FICHEIRO XML
# ==========================================
f = open("glossario_termos.xml", "r", encoding="utf8")
texto = f.read()
f.close() 


# ==========================================
# 2. ACHATAMENTO E LIMPEZA INICIAL
# ==========================================

# Remover tags e manter <b> e <i>
texto = re.sub(r'</?pdf2xml.*?>', ' ', texto)
texto = re.sub(r'</?page.*?>', ' ', texto)
texto = re.sub(r'<fontspec.*?>', ' ', texto)
texto = re.sub(r'</?text.*?>', ' ', texto)

# Limpeza do cabeçalho
texto = re.sub(r'Glossário de Termos.*?Portugal\)', ' ', texto, flags=re.S)
texto = re.sub(r'Fonte:.*?Languages', ' ', texto, flags=re.S)
texto = re.sub(r'Observação:.*?Linguistics\.', ' ', texto, flags=re.S)

# Remover as letras do alfabeto soltas (A, B, C...)
texto = re.sub(r'\b<b>[A-ZÀ-Ú]</b>\b', ' ', texto, flags=re.I)


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

# Colocamos tudo numa única lista garantindo a ordem: (Termo, Definição)
conceitos = [(termo, definicao) for definicao, termo in extraidos_1]
conceitos += [(termo, definicao) for termo, definicao in extraidos_2]

# ==========================================
# 5. CONSTRUÇÃO DO DICIONÁRIO AUXILIAR
# ==========================================
dicionario_medico = {}

for termo_raw, definicao_raw in conceitos:
    
    # Limpar espaços extra e arrancar aspas (simples ou duplas) das pontas
    termo = re.sub(r'\s+', ' ', termo_raw).strip().strip("'\"")
    definicao = re.sub(r'\s+', ' ', definicao_raw).strip()

    if termo and definicao:
        # 1. Proteção contra inversões (ex: acomodação/adaptação)
        if definicao in dicionario_medico and termo in dicionario_medico[definicao]["definicao"]:
            continue
            
        # 2. Juntar definicao ao mesmo termo
        elif termo in dicionario_medico:
            if definicao not in dicionario_medico[termo]["definicao"]:
                dicionario_medico[termo]["definicao"] += f" / {definicao}"
                
        # 3. Termo novo
        else:
            dicionario_medico[termo] = {"definicao": definicao}

# ==========================================
# 6. CONVERSÃO PARA O FORMATO FINAL (LISTA DE OBJETOS)
# ==========================================
lista_final = []
for termo, dados in dicionario_medico.items():
    lista_final.append({
        "termo": termo,
        "definicao": dados["definicao"]
    })

# ==========================================
# 3. EXPORTAR PARA JSON
# ==========================================
def gera_json(filename, dicionario):
    f_out = open(filename, 'w', encoding='utf8')
    json.dump(dicionario, f_out, indent=4, ensure_ascii=False)
    f_out.close()

gera_json("glossario_termos.json", lista_final)
