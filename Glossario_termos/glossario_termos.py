import re
import json

f = open("glossario_termos.xml", "r", encoding="utf8")
texto = f.read()
f.close() 

<<<<<<< HEAD

# ==========================================
# 2. ACHATAMENTO E LIMPEZA INICIAL
# ==========================================

# Remover tags desnecessárias
=======
# Limpeza das tags e manter <b> e <i>
texto = re.sub(r'</?pdf2xml.*?>', ' ', texto)
texto = re.sub(r'</?page.*?>', ' ', texto)
texto = re.sub(r'<fontspec.*?>', ' ', texto)
texto = re.sub(r'</?text.*?>', ' ', texto)

# Limpeza do cabeçalho
texto = re.sub(r'Glossário de Termos.*?Portugal\)', ' ', texto, flags=re.DOTALL)
texto = re.sub(r'Fonte:.*?Languages', ' ', texto, flags=re.DOTALL)
texto = re.sub(r'Observação:.*?Linguistics\.', ' ', texto, flags=re.DOTALL)

<<<<<<< HEAD
# Remover as letras do alfabeto soltas 
texto = re.sub(r'\b<b>[A-ZÀ-Ú]</b>\b', ' ', texto, flags=re.I)

# Corrigir quebras dentro das definições
texto = re.sub(r'</i>\s*<i>', ' ', texto)

#Itálico (Significado) -> "(pop) ," -> Negrito (Termo)
=======
# Remover as letras do alfabeto soltas (A, B, C...)
texto = re.sub(r'\b<b>[A-ZÀ-Ú]</b>\b', ' ', texto, flags=re.IGNORECASE)

texto = re.sub(r'</i>\s*<i>', ' ', texto)

# Padrão 1: Itálico (Significado) -> "(pop) ," -> Negrito (Termo)
padrao_1 = r'<i>([^<]+)</i>\s*\(pop\)\s*,\s*<b>([^<]+)</b>'
extraidos_1 = re.findall(padrao_1, texto, flags=re.DOTALL)

# Negrito (Termo) -> "," -> Itálico (Significado) -> "(pop)"
padrao_2 = r'<b>([^<]+)</b>\s*,\s*<i>([^<]+)</i>\s*\(pop\)'
extraidos_2 = re.findall(padrao_2, texto, flags=re.DOTALL)

# Colocar tudo numa única lista: (Termo, termo_popular)
conceitos = [(termo, termo_popular) for termo_popular, termo in extraidos_1]
conceitos += [(termo, termo_popular) for termo, termo_popular in extraidos_2]


dicionario_medico = {}

for termo_raw, definicao_raw in conceitos:
    
    # Limpar espaços extra e aspas das pontas
    termo = re.sub(r'\s+', ' ', termo_raw).strip().strip("'\"")
    termo_popular = re.sub(r'\s+', ' ', definicao_raw).strip()

    if termo and termo_popular:
            
        # Juntar termo_popular ao mesmo termo
        if termo in dicionario_medico:
            if termo_popular not in dicionario_medico[termo]["termo_popular"]:
                dicionario_medico[termo]["termo_popular"] += f" / {termo_popular}"
                
        # Termo novo
        else:
            dicionario_medico[termo] = {"termo_popular": termo_popular}


lista_final = []
for termo, dados in dicionario_medico.items():
    lista_final.append({
        "termo": termo,
        "termo popular": dados["termo_popular"]
    })


def gera_json(filename, dicionario):
    f_out = open(filename, 'w', encoding='utf8')
    json.dump(dicionario, f_out, indent=4, ensure_ascii=False)
    f_out.close()

gera_json("glossario_termos.json", lista_final)
