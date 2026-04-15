import re
import json

f = open("WIPOPearl_COVID-19_Glossary.xml", "r", encoding="utf8")
texto = f.read()
f.close() 

# Remover as tags do xml
texto = re.sub(r"</?page.*?>", "", texto) 
texto = re.sub(r"<image.*?>", "", texto)
texto = re.sub(r"<fontspec.*?>", "", texto)
texto = re.sub(r"&amp;", "&", texto)

# Remove o título "WIPO Pearl" (font 0) e os cabeçalhos tipo "A" (font 1)
texto = re.sub(r'<text.*font="(0|1)".*>.*</text>\n?', "", texto)

# Termo: asterisco antes e depois (font="8" com tag <b>)
texto = re.sub(r'<text.*font="8".*><b>(.*?)</b></text>\n?', r"*\1*\n", texto)

# Categoria: @ antes (font="11")
texto = re.sub(r'<text.*font="11".*>(.*?)</text>\n?', r"@\1\n", texto)

#  Traducoes: <b> 
texto = re.sub(r"</?text.*?>", "", texto) 
texto = re.sub(r"<i>|</i>", "", texto) # retirar o itálico dos sinónimos

# Limpeza de texto que foi cortado de linha
texto = re.sub(r"-\s*\n\s*", "", texto) # Junta palavras que foram partidas com hífen
texto = re.sub(r'^\s*$', "", texto, flags=re.MULTILINE) # Remove linhas vazias

# caso o nome do termo ocupe duas linhas (junta os dois asteriscos)
texto = re.sub(r'\*\n\*(.*?)\*\n', r' \1*\n', texto)

# Seapara o bloco *Termo* -> Descrição -> @Categoria -> Traduções
padrao = r'\*(.*?)\*\n(.*?)\n@(.*?)\n((?:(?!\*|@).)*)'
correspondencias = re.findall(padrao, texto, re.DOTALL)

glossario = {}

for correspondencia in correspondencias:
    termo = correspondencia[0].strip()
    descricao_raw = correspondencia[1].strip()
    categoria = correspondencia[2].strip()
    traducoes_raw = correspondencia[3].strip()
    
    # Limpar o termo
    termo = termo.replace("*", "").replace("\n", " ").strip()
    
    # --extrair o sinonimo principal--
    sinonimos_principais = []
    descricao = descricao_raw
    
    # capturar o que está entre (syn.) e a próxima quebra de linha
    match_syn = re.match(r'\(syn\.\)\s*(.*?)\n(.*)', descricao_raw, flags=re.IGNORECASE | re.DOTALL)
    
    if match_syn:
        sinonimo_str = match_syn.group(1).strip()
        # os sinonimos sao separados por virgulas
        sinonimos_principais = [s.strip() for s in sinonimo_str.split(',') if s.strip()]
        descricao = match_syn.group(2).strip() 
    else:
        # caso nao tenha sinónimo no início, limpar a tag 
        descricao = re.sub(r"\(syn\.\)", "", descricao)
        
    # Limpar a descrição final
    descricao = re.sub(r"<b>|</b>", "", descricao).replace("\n", " ")
    descricao = re.sub(r'\s+', ' ', descricao).strip()
   
    # -- separar os sinonimos nas traduções --
    partes_trad = re.split(r'<b>\s*(.*?)\s*</b>', traducoes_raw)
    
    traducoes = {}
    i = 1 
    while i < len(partes_trad) - 1:
        lingua = partes_trad[i].strip()
        texto_traducao = partes_trad[i+1].replace("\n", " ")
        texto_traducao = re.sub(r'\s+', ' ', texto_traducao).strip()
        
        # Cortar a string pela palavra "(syn.)" e a vírgula opcional antes dela
        lista_termos = [t.strip() for t in re.split(r',?\s*\(syn\.\)\s*', texto_traducao) if t.strip()]
        
        # O 1º elemento é a tradução principal. O resto são sinónimos (se existirem)
        termo_principal_trad = lista_termos[0] if len(lista_termos) > 0 else ""
        sinonimos_trad = lista_termos[1:] if len(lista_termos) > 1 else []
        
        traducoes[lingua] = {
            "termo": termo_principal_trad,
            "sinonimos": sinonimos_trad
        }
            
        i += 2
        
    glossario[termo] = {
        "sinonimos": sinonimos_principais,
        "definicao": descricao,
        "categoria": categoria,
        "traducoes": traducoes
    }

def gera_json(filename, dicionario):
    f_out = open(filename, 'w', encoding='utf8')
    json.dump(dicionario, f_out, indent=4, ensure_ascii=False)
    f_out.close()

gera_json("wipo.json", glossario)
