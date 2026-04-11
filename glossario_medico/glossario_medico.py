import re
import json

# Abrir o ficheiro XML
f = open("glossario_medico.xml", "r", encoding="utf8")
texto = f.read()
f.close() # É boa prática fechar o ficheiro

# Expressão regular
padrao = re.compile(r'<text[^>]*font="(\d+)"[^>]*>(.*?)</text>', re.DOTALL)
matches = re.findall(padrao, texto)

def limpar_tags(texto):
    return re.sub(r'<[^>]+>', '', texto).strip()

# ALTERAÇÃO AQUI: Usar uma lista para guardar todos os pares
lista_conceitos = [] 
definicao_atual = None

for font, texto_bloco in matches:
    texto_limpo = limpar_tags(texto_bloco)
    
    if not texto_limpo:
        continue
        
    if font == "5":
        definicao_atual = texto_limpo
    elif font == "1" and definicao_atual:
        # ALTERAÇÃO AQUI: Criamos um dicionário novo para cada par e adicionamos à lista
        novo_conceito = {
            "designacao": texto_limpo,
            "definicao": definicao_atual
        }
        lista_conceitos.append(novo_conceito)

        # Reinicia para procurar o próximo par
        definicao_atual = None

def gera_json(filename, dados):
    f_out = open(filename, 'w', encoding='utf8')
    # Passamos a lista completa para o json.dump
    json.dump(dados, f_out, indent=4, ensure_ascii=False)
    f_out.close()

# Chamada da função com a lista
gera_json("glossario_medico.json", lista_conceitos)