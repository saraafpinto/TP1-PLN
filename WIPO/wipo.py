import re
import json

f = open("WIPOPearl_COVID-19_Glossary.xml", "r", encoding="utf8")
texto = f.read()
f.close() 

# Remove as tags de página e imagens
texto = re.sub(r"</?page.*?>", "", texto) 
texto = re.sub(r"<image.*?>", "", texto)
texto = re.sub(r"<fontspec.*?>", "", texto)

# Remove o título "WIPO Pearl" (font 0) e os cabeçalhos tipo "A" (font 1)
texto = re.sub(r'<text.*font="(0|1)".*>.*</text>\n?', "", texto)


# Termo: Põe um asterisco antes e depois (Procura font="8" e a tag <b>)
texto = re.sub(r'<text.*font="8".*><b>(.*?)</b></text>\n?', r"*\1*\n", texto)

# Categoria: Põe uma @ antes (Procura font="11")
texto = re.sub(r'<text.*font="11".*>(.*?)</text>\n?', r"@\1\n", texto)

#  Línguas:  <b> intacto porque nos ajuda a separar as traduções depois
texto = re.sub(r"</?text.*?>", "", texto) 
texto = re.sub(r"<i>|</i>", "", texto) # Tira a marca de itálico dos sinónimos

# Limpeza de texto que foi cortado de linha
texto = re.sub(r"-\s*\n\s*", "", texto) # Junta palavras que foram partidas com hífen
texto = re.sub(r'^\s*$', "", texto, flags=re.MULTILINE) # Remove linhas vazias

# Ajuste caso o nome do termo ocupe duas linhas (junta os dois asteriscos)
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
    
    # Limpar a descrição (tirar o "(syn.)" e o negrito se existir)
    descricao = re.sub(r"\(syn\.\)", "", descricao_raw)
    descricao = re.sub(r"<b>|</b>", "", descricao).replace("\n", " ")
    # Remover espaços duplos
    descricao = re.sub(r'\s+', ' ', descricao).strip()
    
    # O XML tem as siglas das línguas assim: <b> AR</b> ou <b>PT </b>
    # O re.split corta o texto nessas siglas e gera uma lista
    partes_trad = re.split(r'<b>\s*(.*?)\s*</b>', traducoes_raw)
    
    traducoes = {}
    i = 1 
    while i < len(partes_trad) - 1:
        lingua = partes_trad[i].strip()
       # bloco da traducao - tirar o \n
        texto_traducao = partes_trad[i+1].replace("\n", " ")
        texto_traducao = re.sub(r'\s+', ' ', texto_traducao).strip() # Limpa espaços a mais
        
        traducoes[lingua] = texto_traducao
            
        i += 2
        
    glossario[termo] = {
        "definicao": descricao,
        "categoria": categoria,
        "traducoes": traducoes
    }


def gera_json(filename, dicionario):
    f_out = open(filename, 'w', encoding='utf8')
    json.dump(dicionario, f_out, indent=4, ensure_ascii=False)
    f_out.close()

gera_json("wipo.json", glossario)
